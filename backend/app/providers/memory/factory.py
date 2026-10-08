from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.providers.base import ProviderStatus
from app.providers.memory.base import Chunk, MemoryProvider
from app.providers.memory.qdrant_adapter import QdrantMemory


class NullMemory(MemoryProvider):
    """RAG disabled. The agent simply runs without retrieval context."""

    name = "null"
    enabled = False

    async def ingest(self, *, doc_id: str, title: str, text: str) -> int:
        return 0

    async def search(self, query: str, *, k: int = 4) -> list[Chunk]:
        return []

    async def health(self) -> ProviderStatus:
        return ProviderStatus.up(self.name, "RAG disabled (RAG_ENABLED=false).")


def _build() -> MemoryProvider:
    if not settings.rag_enabled:
        return NullMemory()
    provider = settings.memory_provider.lower().strip()
    if provider == "qdrant":
        return QdrantMemory()
    if provider in ("none", "null", ""):
        return NullMemory()
    return NullMemory()


@lru_cache
def get_memory() -> MemoryProvider:
    return _build()
