"""UserStory ORM model for requirement sketch upstream data."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class UserStory(Base):
    """用户故事表 — Sketch 草图的上游数据源."""

    __tablename__ = "user_stories"

    story_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_desc: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="页面描述段落，用于 PageSpec 解析"
    )
    priority: Mapped[str] = mapped_column(String(8), nullable=False, default="P1")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "priority IN ('P0','P1','P2','P3')",
            name="ck_story_priority",
        ),
        CheckConstraint(
            "status IN ('DRAFT','ACTIVE','ARCHIVED')",
            name="ck_story_status",
        ),
    )
