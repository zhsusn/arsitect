"""Sketch ORM model for sketch session container."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Sketch(Base):
    """草图会话表 — 作为 sketch_pages 的容器，记录一次草图生成会话."""

    __tablename__ = "sketches"

    sketch_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_story_ids: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="参与生成的用户故事 ID 列表 JSON"
    )
    page_count: Mapped[int | None] = mapped_column(
        nullable=True, comment="生成页面数"
    )
    coverage_percent: Mapped[int | None] = mapped_column(
        nullable=True, comment="字段覆盖率"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="DRAFT"
    )
    validation_report: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="路径验证报告 JSON"
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT','GENERATING','GENERATED','REVIEW_PENDING','APPROVED','REJECTED','ARCHIVED')",
            name="ck_sketch_status",
        ),
    )
