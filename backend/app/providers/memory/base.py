from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from app.providers.base import ProviderStatus


@dataclass
class Chunk:
    text: str
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryProvider(abc.ABC):
    """Vector memory / RAG. RAG is OPTIONAL — the null provider is a no-op."""

    name: str = "base"
    enabled: bool = True

    @abc.abstractmethod
    async def ingest(self, *, doc_id: str, title: str, text: str) -> int:
        """Chunk + embed + upsert a document. Returns the chunk count."""

    @abc.abstractmethod
    async def search(self, query: str, *, k: int = 4) -> list[Chunk]: ...

    @abc.abstractmethod
    async def health(self) -> ProviderStatus: ...

    @staticmethod
    def chunk_text(text: str, size: int = 800, overlap: int = 120) -> list[str]:
        text = " ".join(text.split())
        if len(text) <= size:
            return [text] if text else []
        out, start = [], 0
        while start < len(text):
            out.append(text[start : start + size])
            start += size - overlap
        return out
