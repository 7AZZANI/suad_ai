from __future__ import annotations

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class AuditLog(UUIDMixin, TimestampMixin, Base):
    """Immutable record of every tool invocation and its policy decision."""

    __tablename__ = "audit_logs"

    subject: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(64))
    tool_name: Mapped[str] = mapped_column(String(64), index=True)
    risk_level: Mapped[str] = mapped_column(String(16))
    decision: Mapped[str] = mapped_column(String(16))  # allowed | denied | approval_required
    arguments: Mapped[dict] = mapped_column(JSON, default=dict)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    result_summary: Mapped[str] = mapped_column(Text, default="")
    agent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
