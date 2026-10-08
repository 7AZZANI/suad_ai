from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Role(UUIDMixin, TimestampMixin, Base):
    """A permission role: the set of scopes it grants.

    Roles seeded from `app/permissions/defaults.py` can be overridden/extended
    here at runtime via the Permissions admin page.
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    # List[str] of scope strings, e.g. ["tools:read", "crm:write"].
    scopes: Mapped[list] = mapped_column(JSON, default=list)
