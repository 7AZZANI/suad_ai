from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Agent(UUIDMixin, TimestampMixin, Base):
    """A configurable AI employee: persona, model knobs, allowed tools."""

    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    system_prompt: Mapped[str] = mapped_column(Text, default="You are a helpful assistant.")
    role: Mapped[str] = mapped_column(String(64), default="operator")
    # Comma-separated tool names this agent may call ("*" = all registered).
    allowed_tools: Mapped[str] = mapped_column(Text, default="*")
    temperature: Mapped[float] = mapped_column(Float, default=0.3)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1024)
    rag_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def allowed_tool_set(self) -> set[str] | None:
        names = {t.strip() for t in self.allowed_tools.split(",") if t.strip()}
        return None if "*" in names else names
