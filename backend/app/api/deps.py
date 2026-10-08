"""Shared FastAPI dependencies."""

from __future__ import annotations

from app.core.security import Identity, get_identity
from app.db.session import get_db

__all__ = ["Identity", "get_identity", "get_db"]
