from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.schemas import IngestRequest, SearchRequest
from app.core.errors import ProviderError, ProviderNotConfigured
from app.db.models import Document
from app.providers.memory import get_memory

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/status")
async def status() -> dict:
    mem = get_memory()
    s = await mem.health()
    return {"enabled": mem.enabled, "ok": s.ok, "provider": s.provider,
            "detail": s.detail}


@router.post("/ingest")
async def ingest(payload: IngestRequest, db: AsyncSession = Depends(get_db)) -> dict:
    mem = get_memory()
    if not mem.enabled:
        raise ProviderNotConfigured(
            "RAG is disabled (RAG_ENABLED=false). Enable Qdrant to ingest."
        )
    doc_id = str(uuid.uuid4())
    count = await mem.ingest(doc_id=doc_id, title=payload.title, text=payload.text)
    try:
        db.add(Document(id=doc_id, title=payload.title, source=payload.source,
                        chunk_count=count, status="ingested",
                        preview=payload.text[:240]))
        await db.commit()
    except Exception:
        pass  # metadata persistence is best-effort
    return {"document_id": doc_id, "chunks": count, "title": payload.title}


@router.post("/search")
async def search(payload: SearchRequest) -> dict:
    mem = get_memory()
    if not mem.enabled:
        return {"enabled": False, "available": False, "results": []}
    try:
        chunks = await mem.search(payload.query, k=payload.k)
    except ProviderError as exc:
        # Graceful degradation: RAG is optional. If the vector store is
        # unreachable, return empty results instead of failing the request.
        return {"enabled": True, "available": False, "results": [],
                "detail": exc.message}
    return {
        "enabled": True,
        "available": True,
        "results": [
            {"text": c.text, "score": c.score, "metadata": c.metadata}
            for c in chunks
        ],
    }


@router.get("/documents")
async def documents(db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (
        await db.execute(select(Document).order_by(Document.created_at.desc()))
    ).scalars().all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "source": d.source,
            "chunks": d.chunk_count,
            "status": d.status,
            "preview": d.preview,
            "created_at": d.created_at.isoformat(),
        }
        for d in rows
    ]
