from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class ApprovalRequest(UUIDMixin, TimestampMixin, Base):
    """A pending human-in-the-loop approval for an `approval`-tier action."""

    __tablename__ = "approval_requests"

    tool_name: Mapped[str] = mapped_column(String(64), index=True)
    subject: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(64))
    arguments: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|approved|rejected
    reason: Mapped[str] = mapped_column(Text, default="")
    decided_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
