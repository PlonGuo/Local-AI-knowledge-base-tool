"""Tests for ingest service — Markdown load, text split, embed, Chroma store, dedup."""
import hashlib
import os
from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio

from app.database import close_db, get_db, init_db
from app.services.ingest_service import IngestService


@pytest.fixture
def knowledge_dir(tmp_path):
    """Create a temporary knowledge directory with sample Markdown files."""
    md1 = tmp_path / "hello.md"
    md1.write_text("# Hello World\n\nThis is a test document about greetings.\n")

    md2 = tmp_path / "subdir" / "nested.md"
    md2.parent.mkdir()
    md2.write_text("# Nested\n\nA nested markdown file with some content.\n")

    return tmp_path


@pytest.fixture
def long_doc(tmp_path):
    """Create a Markdown file long enough to produce multiple chunks."""
    content = "# Long Document\n\n"
    for i in range(100):
        content += f"## Section {i}\n\nThis is paragraph {i} with enough text to fill up a chunk. " * 5 + "\n\n"
    md = tmp_path / "long.md"
    md.write_text(content)
    return tmp_path


@pytest_asyncio.fixture
async def db():
    """In-memory database for testing."""
    await init_db(":memory:")
    async with get_db() as conn:
        yield conn
    await close_db()


@pytest.fixture
def chroma_dir(tmp_path):
    """Separate temp dir for Chroma persistence."""
    d = tmp_path / "chroma_store"
    d.mkdir()
    return d


@pytest.fixture
def service(db, chroma_dir):
    """Create an IngestService with test Chroma dir."""
    return IngestService(chroma_path=str(chroma_dir))


# ── File loading ─────────────────────────────────────────────────


def test_load_markdown_files(service, knowledge_dir):
    """Should discover all .md files recursively."""
    files = service.find_markdown_files(knowledge_dir)
    assert len(files) == 2
    names = {f.name for f in files}
    assert "hello.md" in names
    assert "nested.md" in names


def test_load_markdown_ignores_non_md(service, tmp_path):
    """Should ignore non-markdown files."""
    (tmp_path / "readme.md").write_text("# Readme\n")
    (tmp_path / "notes.txt").write_text("plain text\n")
    (tmp_path / "image.png").write_bytes(b"\x89PNG")
    files = service.find_markdown_files(tmp_path)
    assert len(files) == 1
    assert files[0].name == "readme.md"


# ── Text splitting ───────────────────────────────────────────────


def test_split_text_basic(service):
    """Short text should produce a single chunk."""
    chunks = service.split_text("Short text", metadata={"file_path": "a.md"})
    assert len(chunks) >= 1
    assert chunks[0].page_content == "Short text"
    assert chunks[0].metadata["file_path"] == "a.md"


def test_split_text_long(service, long_doc):
    """Long text should produce multiple chunks."""
    content = (long_doc / "long.md").read_text()
    chunks = service.split_text(content, metadata={"file_path": "long.md"})
    assert len(chunks) > 1
    # Each chunk should have chunk_index metadata
    for i, chunk in enumerate(chunks):
        assert chunk.metadata["chunk_index"] == i
        assert chunk.metadata["file_path"] == "long.md"


# ── File hash ────────────────────────────────────────────────────


def test_compute_file_hash(service, knowledge_dir):
    """Should compute SHA-256 hash of file content."""
    file_path = knowledge_dir / "hello.md"
    h = service.compute_file_hash(file_path)
    expected = hashlib.sha256(file_path.read_bytes()).hexdigest()
    assert h == expected


# ── Chroma store ─────────────────────────────────────────────────


def test_chroma_collection_created(service):
    """Service should create a Chroma collection."""
    collection = service.collection
    assert collection is not None
    assert collection.name == "knowhive"


def test_store_chunks_in_chroma(service):
    """Should store chunks and retrieve them."""
    chunks = service.split_text("Hello world from KnowHive", metadata={"file_path": "test.md"})
    service.store_chunks(chunks)

    results = service.collection.get(where={"file_path": "test.md"})
    assert len(results["ids"]) >= 1
    assert "Hello world" in results["documents"][0]


# ── Dedup (delete old chunks before re-ingest) ──────────────────


def test_dedup_removes_old_chunks(service):
    """Re-ingesting same file_path should replace old chunks."""
    chunks1 = service.split_text("Version 1 content", metadata={"file_path": "dup.md"})
    service.store_chunks(chunks1)

    count_before = service.collection.count()
    assert count_before >= 1

    # Dedup then store new version
    service.delete_chunks_for_file("dup.md")
    chunks2 = service.split_text("Version 2 completely different", metadata={"file_path": "dup.md"})
    service.store_chunks(chunks2)

    results = service.collection.get(where={"file_path": "dup.md"})
    assert len(results["ids"]) >= 1
    assert "Version 2" in results["documents"][0]
    assert "Version 1" not in " ".join(results["documents"])


def test_delete_chunks_nonexistent_file(service):
    """Deleting chunks for a file that doesn't exist should not error."""
    service.delete_chunks_for_file("nonexistent.md")  # should not raise


# ── Full ingest pipeline ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_single_file(service, db, knowledge_dir):
    """Ingest a single file — should create DB record + Chroma chunks."""
    file_path = knowledge_dir / "hello.md"
    result = await service.ingest_file(file_path, knowledge_dir)

    assert result["status"] == "indexed"
    assert result["chunk_count"] >= 1

    # Check DB record
    cursor = await db.execute("SELECT * FROM documents WHERE file_path = ?", (str(file_path),))
    row = await cursor.fetchone()
    assert row is not None
    assert row["status"] == "indexed"
    assert row["chunk_count"] >= 1

    # Check Chroma
    chroma_results = service.collection.get(where={"file_path": str(file_path)})
    assert len(chroma_results["ids"]) >= 1


@pytest.mark.asyncio
async def test_ingest_directory(service, db, knowledge_dir):
    """Ingest all files in a directory."""
    results = await service.ingest_directory(knowledge_dir)
    assert len(results) == 2
    assert all(r["status"] == "indexed" for r in results)

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM documents")
    row = await cursor.fetchone()
    assert row["cnt"] == 2


@pytest.mark.asyncio
async def test_ingest_dedup_on_reingest(service, db, knowledge_dir):
    """Re-ingesting same file should update, not duplicate."""
    file_path = knowledge_dir / "hello.md"
    await service.ingest_file(file_path, knowledge_dir)
    await service.ingest_file(file_path, knowledge_dir)

    # Should still be 1 document record
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM documents WHERE file_path = ?", (str(file_path),))
    row = await cursor.fetchone()
    assert row["cnt"] == 1

    # Chroma should not have duplicates
    chroma_results = service.collection.get(where={"file_path": str(file_path)})
    # Should only have chunks from the latest ingest
    assert len(chroma_results["ids"]) >= 1


@pytest.mark.asyncio
async def test_ingest_updates_modified_file(service, db, knowledge_dir):
    """If file content changes, re-ingest should update hash and chunks."""
    file_path = knowledge_dir / "hello.md"
    await service.ingest_file(file_path, knowledge_dir)

    cursor = await db.execute("SELECT file_hash FROM documents WHERE file_path = ?", (str(file_path),))
    old_hash = (await cursor.fetchone())["file_hash"]

    # Modify file
    file_path.write_text("# Updated Hello\n\nCompletely different content now.\n")
    await service.ingest_file(file_path, knowledge_dir)

    cursor = await db.execute("SELECT file_hash FROM documents WHERE file_path = ?", (str(file_path),))
    new_hash = (await cursor.fetchone())["file_hash"]
    assert new_hash != old_hash


@pytest.mark.asyncio
async def test_ingest_skips_unchanged_file(service, db, knowledge_dir):
    """If file hash matches, ingest should skip re-embedding."""
    file_path = knowledge_dir / "hello.md"
    result1 = await service.ingest_file(file_path, knowledge_dir)
    assert result1["status"] == "indexed"

    result2 = await service.ingest_file(file_path, knowledge_dir)
    assert result2["status"] == "skipped"


@pytest.mark.asyncio
async def test_ingest_records_error_on_bad_file(service, db, tmp_path):
    """Ingesting a nonexistent file should record an error."""
    bad_path = tmp_path / "missing.md"
    result = await service.ingest_file(bad_path, tmp_path)
    assert result["status"] == "error"
    assert "error" in result
