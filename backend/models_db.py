"""ORM models."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    answers_json: Mapped[str] = mapped_column(Text)
    report_json: Mapped[str] = mapped_column(Text)
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)
