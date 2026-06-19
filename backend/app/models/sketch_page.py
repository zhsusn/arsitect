"""SketchPage ORM model for generated low-fi sketch pages."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class SketchPage(Base):
    """草图页面表 — 存储基于用户故事生成的低保真草图."""

    __tablename__ = "sketch_pages"

    page_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    story_id: Mapped[str | None] = mapped_column(
        ForeignKey("user_stories.story_id", ondelete="SET NULL"),
        nullable=True,
    )
    page_name: Mapped[str] = mapped_column(String(128), nullable=False)
    page_type: Mapped[str] = mapped_column(String(16), nullable=False, default="UNKNOWN")
    svg_content: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="生成的 SVG 草图内容"
    )
    fields_json: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="页面字段列表 JSON"
    )
    buttons_json: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="页面按钮/操作列表 JSON"
    )
    nav_targets_json: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="跳转目标页面列表 JSON"
    )
    source_module_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="来源模块编号 DR-XXX"
    )
    source_md_path: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="来源 module-requirements.md 路径"
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "page_type IN ('LIST','DETAIL','DASHBOARD','FORM','MODAL','SEARCH','WIZARD','UNKNOWN')",
            name="ck_sketch_page_type",
        ),
        CheckConstraint(
            "status IN ('DRAFT','GENERATED','REVIEW_PENDING','APPROVED','REJECTED')",
            name="ck_sketch_page_status",
        ),
    )
