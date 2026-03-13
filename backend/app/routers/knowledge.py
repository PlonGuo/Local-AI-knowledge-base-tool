"""Knowledge API endpoints — GET /knowledge/tree, GET /knowledge/file."""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter()

_knowledge_dir: Optional[str] = None


def init_knowledge_router(knowledge_dir: str = "./knowledge") -> None:
    """Initialize knowledge router with the knowledge directory path."""
    global _knowledge_dir
    _knowledge_dir = knowledge_dir


def _get_knowledge_path() -> Path:
    if _knowledge_dir is None:
        raise RuntimeError("Knowledge router not initialized. Call init_knowledge_router() first.")
    return Path(_knowledge_dir)


def _build_tree(directory: Path, base: Path) -> dict:
    """Recursively build a file tree dict for a directory."""
    children = []
    try:
        entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        entries = []

    for entry in entries:
        rel = entry.relative_to(base)
        if entry.is_dir():
            children.append(
                {
                    "name": entry.name,
                    "path": str(rel),
                    "type": "directory",
                    "children": _build_tree(entry, base)["children"],
                }
            )
        else:
            children.append(
                {
                    "name": entry.name,
                    "path": str(rel),
                    "type": "file",
                }
            )

    return {"children": children}


@router.get("/knowledge/tree")
def knowledge_tree() -> dict:
    """Return a file tree JSON of the knowledge directory."""
    root = _get_knowledge_path()
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
    tree = _build_tree(root, root)
    tree["name"] = root.name
    tree["path"] = ""
    tree["type"] = "directory"
    return tree


@router.get("/knowledge/file")
def knowledge_file(path: str = Query(..., description="Relative path within knowledge dir")) -> dict:
    """Return the content of a file in the knowledge directory (read-only)."""
    # Block absolute paths
    if path.startswith("/"):
        raise HTTPException(status_code=400, detail="Absolute paths are not allowed")

    root = _get_knowledge_path()
    resolved = (root / path).resolve()

    # Block path traversal
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Path traversal is not allowed")

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        content = resolved.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")

    return {
        "name": resolved.name,
        "path": path,
        "content": content,
    }
