from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Document(UUIDMixin, TimestampMixin, Base):
    """Metadata for a knowledge-base document ingested into the vector store."""

    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(255), default="upload")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(24), default="ingested")
    preview: Mapped[str] = mapped_column(Text, default="")
