from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class CallLog(UUIDMixin, TimestampMixin, Base):
    """Inbound/outbound telephony session record (provider-agnostic)."""

    __tablename__ = "call_logs"

    provider: Mapped[str] = mapped_column(String(32))
    direction: Mapped[str] = mapped_column(String(16), default="inbound")
    from_number: Mapped[str] = mapped_column(String(40), default="")
    to_number: Mapped[str] = mapped_column(String(40), default="")
    status: Mapped[str] = mapped_column(String(24), default="received")
    agent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    transcript: Mapped[str] = mapped_column(Text, default="")
    provider_payload: Mapped[dict] = mapped_column(JSON, default=dict)
