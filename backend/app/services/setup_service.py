"""Provider connectivity tests powering the Setup Wizard.

Every check returns a uniform ProviderStatus dict so the UI renders them
identically and a failing optional provider never crashes the page.
"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.db.session import ping as db_ping
from app.providers.base import ProviderStatus
from app.providers.llm import get_llm
from app.providers.memory import get_memory
from app.providers.stt import get_stt
from app.providers.telephony import get_telephony
from app.providers.tts import get_tts


def _status_dict(s: ProviderStatus) -> dict[str, Any]:
    return {"ok": s.ok, "provider": s.provider, "detail": s.detail, **s.extra}


async def test_llm() -> dict[str, Any]:
    return _status_dict(await get_llm().health())


async def test_stt() -> dict[str, Any]:
    return _status_dict(await get_stt().health())


async def test_tts() -> dict[str, Any]:
    return _status_dict(await get_tts().health())


async def test_memory() -> dict[str, Any]:
    return _status_dict(await get_memory().health())


async def test_database() -> dict[str, Any]:
    backend = "sqlite" if settings.database_url.startswith("sqlite") else "postgres"
    try:
        await db_ping()
        return {"ok": True, "provider": backend,
                "detail": "Connected.", "url": settings.public_summary()["database"]}
    except Exception as exc:
        return {"ok": False, "provider": backend,
                "detail": f"Unavailable: {exc}",
                "hint": "Run `make docker-up` or set DATABASE_URL to SQLite."}


async def test_telephony() -> dict[str, Any]:
    try:
        return {"ok": True, **get_telephony().status()}
    except Exception as exc:
        return {"ok": False, "provider": settings.telephony_provider,
                "detail": str(exc)}


async def run_all() -> dict[str, Any]:
    return {
        "llm": await test_llm(),
        "stt": await test_stt(),
        "tts": await test_tts(),
        "memory": await test_memory(),
        "database": await test_database(),
        "telephony": await test_telephony(),
    }
