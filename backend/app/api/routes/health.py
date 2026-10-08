from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import settings
from app.db.session import ping

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Liveness — the process is up. Never touches dependencies."""
    return {"status": "ok", "app": settings.app_name, "version": __version__}


@router.get("/ready")
async def ready() -> dict:
    """Readiness — reports dependency status without failing the request."""
    try:
        await ping()
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "env": settings.app_env,
    }
