"""Lightweight identity + secret helpers.

This is intentionally simple and self-hosted-friendly: an optional API key
header maps a caller to a role. Swap in OIDC/JWT later without touching the
permission engine — it only consumes the resulting ``Identity``.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from fastapi import Header

from app.core.config import settings


@dataclass(frozen=True)
class Identity:
    """The authenticated (or anonymous) caller and their role."""

    subject: str
    role: str

    @property
    def is_anonymous(self) -> bool:
        return self.subject == "anonymous"


async def get_identity(
    x_api_key: str | None = Header(default=None),
    x_role: str | None = Header(default=None),
) -> Identity:
    """Resolve the caller identity for a request.

    For local-first usage we accept an optional ``X-Role`` header so the admin
    UI can exercise different roles. In production, replace this dependency
    with real authentication; everything downstream only needs an ``Identity``.
    """
    if x_api_key:
        subject = "api:" + hashlib.sha256(x_api_key.encode()).hexdigest()[:12]
        return Identity(subject=subject, role=x_role or settings.default_role)
    return Identity(subject="anonymous", role=x_role or settings.default_role)


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


def hash_secret(value: str) -> str:
    """One-way hash for storing approval tokens / API keys at rest."""
    return hashlib.sha256((settings.secret_key + value).encode()).hexdigest()
