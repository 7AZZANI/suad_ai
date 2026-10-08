"""Shared provider primitives.

Every adapter (LLM/STT/TTS/telephony/memory) implements ``health()`` and
returns a uniform :class:`ProviderStatus`, so the setup page can probe any
provider the same way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderStatus:
    ok: bool
    provider: str
    detail: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def up(cls, provider: str, detail: str = "", **extra: Any) -> ProviderStatus:
        return cls(ok=True, provider=provider, detail=detail, extra=extra)

    @classmethod
    def down(cls, provider: str, detail: str, **extra: Any) -> ProviderStatus:
        return cls(ok=False, provider=provider, detail=detail, extra=extra)
