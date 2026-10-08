"""Async database engine, session factory and dependency.

The engine is created lazily so the API can boot even when Postgres is not
running yet (the admin UI still loads; DB-backed calls return a clean
``ProviderError``). For local development without Postgres, set
``DATABASE_URL`` to a SQLite URL, e.g.
``sqlite+aiosqlite:///./data/suad.db``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.errors import AppError, ProviderError
from app.core.logging import get_logger
from app.db.base import Base

logger = get_logger("app.db")

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine, _sessionmaker
    if _engine is None:
        logger.info("creating db engine")
        _engine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            future=True,
        )
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        get_engine()
    assert _sessionmaker is not None
    return _sessionmaker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a transactional session."""
    maker = get_sessionmaker()
    async with maker() as session:
        try:
            yield session
        except AppError:
            # Structured app/provider errors must reach the client as-is —
            # never re-labelled as a database failure.
            raise
        except SQLAlchemyError as exc:  # pragma: no cover - connection failures
            raise ProviderError(
                "Database is unavailable.",
                {"hint": "Is Postgres running? Check DATABASE_URL.",
                 "cause": str(exc)},
            ) from exc


async def init_models() -> None:
    """Create tables directly (used for SQLite/dev/tests; prod uses Alembic)."""
    engine = get_engine()
    # Import models so they register on Base.metadata.
    from app.db import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("db tables ensured")


async def ping() -> bool:
    """Cheap connectivity check for /ready and the setup tester."""
    from sqlalchemy import text

    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return True
