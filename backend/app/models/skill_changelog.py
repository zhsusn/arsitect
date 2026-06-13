"""Skill DAG changelog ORM model."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class SkillChangeLog(Base):
    """DAG edit operation audit log."""

    __tablename__ = "skill_change_logs"

    log_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    before_snapshot: Mapped[str | None] = mapped_column(
        String(4096), nullable=True
    )
    after_snapshot: Mapped[str | None] = mapped_column(
        String(4096), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        {"sqlite_autoincrement": False},
    )
