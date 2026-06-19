"""Skill ORM model."""

from __future__ import annotations

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin


class Skill(Base, TimestampMixin):
    """Skill registry table."""

    __tablename__ = "skills"

    skill_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    skill_name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    pattern: Mapped[str] = mapped_column(String(32), nullable=False)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    platforms: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    directory_path: Mapped[str] = mapped_column(String(4096), nullable=False)
    parse_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PARSED")
    parse_error_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    __table_args__ = (
        UniqueConstraint("skill_name", "version", name="uq_skill_name_version"),
        {"sqlite_autoincrement": False},
    )
