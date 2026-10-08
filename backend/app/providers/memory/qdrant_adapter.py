"""Qdrant-backed vector memory. qdrant-client imported lazily."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.config import settings
from app.core.errors import ProviderError
from app.core.logging import get_logger
from app.providers.base import ProviderStatus
from app.providers.memory.base import Chunk, MemoryProvider
from app.providers.memory.embeddings import embed_texts

logger = get_logger("app.memory.qdrant")


class QdrantMemory(MemoryProvider):
    name = "qdrant"
    enabled = True

    def __init__(self) -> None:
        self._client: Any | None = None
        self._ready = False

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
            except ImportError as exc:  # pragma: no cover
                raise ProviderError(
                    "qdrant-client not installed. `pip install qdrant-client` "
                    "or set RAG_ENABLED=false.",
                ) from exc
            self._client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key or None,
            )
        return self._client

    @staticmethod
    def _models() -> Any:
        """Lazily import qdrant_client.models with a friendly error."""
        try:
            from qdrant_client import models
        except ImportError as exc:  # pragma: no cover
            raise ProviderError(
                "qdrant-client not installed. `pip install qdrant-client` "
                "or set RAG_ENABLED=false.",
            ) from exc
        return models

    def _ensure_collection(self) -> None:
        if self._ready:
            return
        models = self._models()
        Distance, VectorParams = models.Distance, models.VectorParams

        client = self._get_client()
        existing = {c.name for c in client.get_collections().collections}
        if settings.qdrant_collection not in existing:
            client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(
                    size=settings.embedding_dim, distance=Distance.COSINE
                ),
            )
        self._ready = True

    async def ingest(self, *, doc_id: str, title: str, text: str) -> int:
        chunks = self.chunk_text(text)
        if not chunks:
            return 0
        try:
            point_struct = self._models().PointStruct
            self._ensure_collection()
            vectors = await embed_texts(chunks)
            points = [
                point_struct(
                    id=str(uuid.uuid4()),
                    vector=vec,
                    payload={"doc_id": doc_id, "title": title, "text": chunk},
                )
                for chunk, vec in zip(chunks, vectors, strict=False)
            ]
            self._get_client().upsert(
                collection_name=settings.qdrant_collection, points=points
            )
        except ProviderError:
            raise
        except Exception as exc:  # pragma: no cover - network dependent
            raise ProviderError("Qdrant ingest failed.", {"cause": str(exc)}) from exc
        return len(chunks)

    async def search(self, query: str, *, k: int = 4) -> list[Chunk]:
        try:
            self._ensure_collection()
            vec = (await embed_texts([query]))[0]
            hits = self._get_client().search(
                collection_name=settings.qdrant_collection,
                query_vector=vec,
                limit=k,
            )
        except ProviderError:
            raise
        except Exception as exc:  # pragma: no cover - network dependent
            raise ProviderError("Qdrant search failed.", {"cause": str(exc)}) from exc
        return [
            Chunk(
                text=h.payload.get("text", ""),
                score=float(h.score),
                metadata={k2: v for k2, v in h.payload.items() if k2 != "text"},
            )
            for h in hits
        ]

    async def health(self) -> ProviderStatus:
        try:
            client = self._get_client()
            client.get_collections()
            return ProviderStatus.up(self.name, f"url={settings.qdrant_url}")
        except Exception as exc:  # pragma: no cover
            return ProviderStatus.down(
                self.name, f"Unreachable: {exc}", url=settings.qdrant_url
            )
