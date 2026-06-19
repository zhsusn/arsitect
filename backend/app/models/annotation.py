"""Annotation ORM model for stage annotations / reviews."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Annotation(Base):
    """A review annotation attached to a project stage."""

    __tablename__ = "annotations"

    annotation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    stage_id: Mapped[str] = mapped_column(
        ForeignKey("project_stages.project_stage_id", ondelete="CASCADE"),
        nullable=False,
    )
    author: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    annotation_type: Mapped[str] = mapped_column(String(16), nullable=False, default="comment")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="REVIEW_PENDING")
    viewed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
