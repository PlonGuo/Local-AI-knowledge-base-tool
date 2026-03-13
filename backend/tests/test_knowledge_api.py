"""Tests for knowledge API endpoints — GET /knowledge/tree, GET /knowledge/file."""
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.database import close_db, init_db
from app.main import create_app


@pytest_asyncio.fixture
async def db():
    """In-memory database for testing."""
    await init_db(":memory:")
    yield
    await close_db()


@pytest.fixture
def knowledge_dir(tmp_path):
    """Create a temporary knowledge directory with sample Markdown files."""
    # Root-level file
    (tmp_path / "readme.md").write_text("# Readme\n\nTop-level doc.\n")

    # Subdirectory with files
    sub = tmp_path / "guides"
    sub.mkdir()
    (sub / "getting-started.md").write_text("# Getting Started\n\nStep 1.\n")
    (sub / "advanced.md").write_text("# Advanced\n\nDeep dive.\n")

    # Nested subdirectory
    deep = sub / "extras"
    deep.mkdir()
    (deep / "tips.md").write_text("# Tips\n\nUseful tips.\n")

    # Non-markdown file (should still appear in tree)
    (tmp_path / "notes.txt").write_text("plain text notes")

    return tmp_path


@pytest.fixture
def app(db, knowledge_dir, tmp_path):
    """Create a FastAPI test app with knowledge router configured."""
    config_path = tmp_path / "config.yaml"
    application = create_app(config_path=config_path)

    from app.routers.knowledge import init_knowledge_router

    init_knowledge_router(knowledge_dir=str(knowledge_dir))

    return application


@pytest.fixture
def client(app):
    return TestClient(app)


# ── GET /knowledge/tree ──────────────────────────────────────────


def test_tree_returns_200(client):
    """GET /knowledge/tree should return 200."""
    resp = client.get("/knowledge/tree")
    assert resp.status_code == 200


def test_tree_root_has_children(client):
    """Tree root should contain files and directories."""
    data = client.get("/knowledge/tree").json()
    assert "children" in data
    names = [c["name"] for c in data["children"]]
    assert "readme.md" in names
    assert "guides" in names
    assert "notes.txt" in names


def test_tree_directories_have_children(client):
    """Directories in the tree should have a children list."""
    data = client.get("/knowledge/tree").json()
    guides = next(c for c in data["children"] if c["name"] == "guides")
    assert guides["type"] == "directory"
    assert "children" in guides
    child_names = [c["name"] for c in guides["children"]]
    assert "getting-started.md" in child_names
    assert "advanced.md" in child_names
    assert "extras" in child_names


def test_tree_nested_directory(client):
    """Nested directories should appear in the tree."""
    data = client.get("/knowledge/tree").json()
    guides = next(c for c in data["children"] if c["name"] == "guides")
    extras = next(c for c in guides["children"] if c["name"] == "extras")
    assert extras["type"] == "directory"
    child_names = [c["name"] for c in extras["children"]]
    assert "tips.md" in child_names


def test_tree_files_have_type(client):
    """Files should have type='file'."""
    data = client.get("/knowledge/tree").json()
    readme = next(c for c in data["children"] if c["name"] == "readme.md")
    assert readme["type"] == "file"


def test_tree_files_have_path(client):
    """Each node should include a relative path."""
    data = client.get("/knowledge/tree").json()
    readme = next(c for c in data["children"] if c["name"] == "readme.md")
    assert readme["path"] == "readme.md"

    guides = next(c for c in data["children"] if c["name"] == "guides")
    started = next(c for c in guides["children"] if c["name"] == "getting-started.md")
    assert started["path"] == "guides/getting-started.md"


def test_tree_sorted_dirs_first(client):
    """Directories should appear before files, both sorted alphabetically."""
    data = client.get("/knowledge/tree").json()
    children = data["children"]
    dirs = [c for c in children if c["type"] == "directory"]
    files = [c for c in children if c["type"] == "file"]
    # Dirs come first in the list
    if dirs and files:
        last_dir_idx = max(children.index(d) for d in dirs)
        first_file_idx = min(children.index(f) for f in files)
        assert last_dir_idx < first_file_idx


# ── GET /knowledge/file ──────────────────────────────────────────


def test_file_returns_content(client):
    """GET /knowledge/file?path=readme.md should return file content."""
    resp = client.get("/knowledge/file", params={"path": "readme.md"})
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert "# Readme" in data["content"]


def test_file_nested_path(client):
    """GET /knowledge/file with nested path should work."""
    resp = client.get("/knowledge/file", params={"path": "guides/getting-started.md"})
    assert resp.status_code == 200
    assert "# Getting Started" in resp.json()["content"]


def test_file_deep_nested(client):
    """GET /knowledge/file with deeply nested path should work."""
    resp = client.get("/knowledge/file", params={"path": "guides/extras/tips.md"})
    assert resp.status_code == 200
    assert "# Tips" in resp.json()["content"]


def test_file_not_found(client):
    """GET /knowledge/file with nonexistent path should return 404."""
    resp = client.get("/knowledge/file", params={"path": "nonexistent.md"})
    assert resp.status_code == 404


def test_file_path_traversal_blocked(client):
    """Path traversal attempts should be blocked."""
    resp = client.get("/knowledge/file", params={"path": "../../../etc/passwd"})
    assert resp.status_code == 400


def test_file_absolute_path_blocked(client):
    """Absolute paths should be blocked."""
    resp = client.get("/knowledge/file", params={"path": "/etc/passwd"})
    assert resp.status_code == 400


def test_file_missing_path_param(client):
    """GET /knowledge/file without path param should return 422."""
    resp = client.get("/knowledge/file")
    assert resp.status_code == 422


def test_file_returns_filename(client):
    """Response should include the file name."""
    resp = client.get("/knowledge/file", params={"path": "readme.md"})
    data = resp.json()
    assert data["name"] == "readme.md"
    assert data["path"] == "readme.md"
