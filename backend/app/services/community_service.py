"""CommunityService — fetch community content manifest, import packs."""
import time
from pathlib import Path
from typing import Any, Optional

import httpx
from pydantic import BaseModel

# Default manifest URL (GitHub raw)
MANIFEST_URL = "https://raw.githubusercontent.com/PlonGuo/knowhive-community/main/manifest.json"
DEFAULT_CACHE_TTL = 300  # 5 minutes


class ContentPack(BaseModel):
    id: str
    name: str
    description: str
    author: str
    tags: list[str]
    file_count: int
    size_kb: int
    path: str


class CommunityManifest(BaseModel):
    version: str
    packs: list[ContentPack]


class PackFile(BaseModel):
    filename: str
    path: str
    size_kb: int


class CommunityService:
    """Fetches and caches community content manifests; imports packs."""

    def __init__(
        self,
        knowledge_dir: Path,
        manifest_url: str = MANIFEST_URL,
        cache_ttl: int = DEFAULT_CACHE_TTL,
    ):
        self._knowledge_dir = knowledge_dir
        self._manifest_url = manifest_url
        self._cache_ttl = cache_ttl
        self._cached_manifest: Optional[CommunityManifest] = None
        self._cache_time: float = 0.0

    async def fetch_manifest(self) -> CommunityManifest:
        """Fetch and cache the community manifest. Respects TTL."""
        now = time.monotonic()
        if self._cached_manifest is not None and (now - self._cache_time) < self._cache_ttl:
            return self._cached_manifest

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(self._manifest_url)
            resp.raise_for_status()
            data = resp.json()

        self._cached_manifest = CommunityManifest(**data)
        self._cache_time = now
        return self._cached_manifest

    async def fetch_pack_files(self, pack: ContentPack) -> list[PackFile]:
        """Fetch the file listing for a content pack."""
        # files.json is at {pack.path}/files.json in the community repo
        base = self._manifest_url.rsplit("/manifest.json", 1)[0]
        files_url = f"{base}/{pack.path}/files.json"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(files_url)
            resp.raise_for_status()
            data = resp.json()
        return [PackFile(**f) for f in data]
