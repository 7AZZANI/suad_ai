"""Application entrypoint.

Run: `make dev`  ->  uvicorn app.main:app --reload
Docs UI: http://localhost:8000/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import (
    agents,
    health,
    memory,
    permissions,
    setup,
    tasks,
    telephony,
)
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import get_logger
from app.tools.builtin import register_builtin_tools

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_builtin_tools()
    logger.info("starting app=%s env=%s llm=%s", settings.app_name,
                settings.app_env, settings.llm_provider)
    # Best-effort schema bootstrap for local/SQLite. Postgres uses Alembic
    # (`make migrate`); a failure here must NOT prevent the API from booting.
    try:
        from app.db.session import init_models

        await init_models()
    except Exception as exc:  # pragma: no cover
        logger.warning("db bootstrap skipped: %s", exc)
    yield
    logger.info("shutting down")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Local-first, cloud-optional AI voice-agent platform.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

for module in (health, setup, agents, tasks, permissions, memory, telephony):
    app.include_router(module.router)


@app.get("/", tags=["root"])
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }
