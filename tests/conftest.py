"""Test fixtures. The whole suite runs with zero external services."""

from __future__ import annotations

import os

# Force a self-contained SQLite DB before any app module imports settings.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./data/test.db")
os.environ.setdefault("RAG_ENABLED", "true")

import pytest  # noqa: E402

from app.core.config import settings  # noqa: E402


@pytest.fixture
def patch_settings(monkeypatch):
    """Patch settings attributes and clear provider factory caches."""

    from app.providers.llm.factory import get_llm
    from app.providers.memory.factory import get_memory
    from app.providers.stt.factory import get_stt
    from app.providers.telephony.factory import get_telephony
    from app.providers.tts.factory import get_tts

    def _apply(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setattr(settings, key, value)
        for fn in (get_llm, get_stt, get_tts, get_memory, get_telephony):
            fn.cache_clear()
        return settings

    yield _apply
    for fn in (get_llm, get_stt, get_tts, get_memory, get_telephony):
        fn.cache_clear()
