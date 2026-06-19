"""Wireframe ORM model for wireframe session container."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Wireframe(Base):
    """线框图会话表 — 作为 wireframe_pages 的容器，记录一次三阶段流水线会话."""

    __tablename__ = "wireframes"

    wireframe_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    c4_baseline_version: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="关联的 C4 Baseline 版本"
    )
    pipeline_stage: Mapped[str] = mapped_column(String(16), nullable=False, default="idle")
    page_count: Mapped[int | None] = mapped_column(nullable=True, comment="生成页面数")
    avg_confidence: Mapped[int | None] = mapped_column(nullable=True, comment="平均映射置信度")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "pipeline_stage IN ('idle','domain_mapping','mapping_review','layout_planning','nav_linking','completed','failed_domain','failed_layout','failed_nav')",
            name="ck_wireframe_pipeline_stage",
        ),
        CheckConstraint(
            "status IN ('DRAFT','ACTIVE','ARCHIVED')",
            name="ck_wireframe_status",
        ),
    )
