"""Embedding helper.

Uses any OpenAI-compatible `/embeddings` endpoint (Ollama's
`nomic-embed-text`, OpenAI `text-embedding-3-*`, etc.) over plain httpx so we
don't add a hard SDK dependency for RAG.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.errors import ProviderError


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    url = settings.embedding_base_url.rstrip("/") + "/embeddings"
    headers = {"Authorization": f"Bearer {settings.embedding_api_key or 'local'}"}
    payload = {"model": settings.embedding_model, "input": texts}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return [item["embedding"] for item in data["data"]]
    except Exception as exc:  # pragma: no cover - network dependent
        raise ProviderError(
            "Embedding request failed.",
            {"endpoint": url, "model": settings.embedding_model, "cause": str(exc)},
        ) from exc
