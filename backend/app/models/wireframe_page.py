"""WireframePage ORM model for generated SVG wireframe pages."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class WireframePage(Base):
    """线框图页面表 — 存储 DomainMapper + LayoutPlanner 生成的单页 SVG."""

    __tablename__ = "wireframe_pages"

    page_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    wireframe_id: Mapped[str] = mapped_column(
        ForeignKey("wireframes.wireframe_id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="关联的 C4 领域实体标识"
    )
    entity_name: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="领域实体名称"
    )
    page_name: Mapped[str] = mapped_column(String(128), nullable=False)
    page_type: Mapped[str] = mapped_column(String(16), nullable=False, default="UNKNOWN")
    confidence: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="DomainMapper 置信度 0-100"
    )
    mapping_source: Mapped[str] = mapped_column(String(16), nullable=False, default="auto")
    svg_content: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="生成的 SVG 线框图内容"
    )
    layout_json: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="布局坐标与元素占位 JSON"
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING_MAPPING")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "page_type IN ('LIST','DETAIL','DASHBOARD','FORM','MODAL','SEARCH','WIZARD','UNKNOWN')",
            name="ck_wf_page_type",
        ),
        CheckConstraint(
            "mapping_source IN ('auto','manual','low_conf','uncertain')",
            name="ck_wf_mapping_source",
        ),
        CheckConstraint(
            "status IN ('PENDING_MAPPING','MAPPED_AUTO','MAPPED_LOW_CONF','MAPPED_UNCERTAIN','MAPPED_CONFIRMED','MAPPED_CORRECTED','LAYOUT_GENERATED','NAV_LINKED','PUBLISHED','ERROR_LAYOUT','ERROR_NAV','ARCHIVED')",
            name="ck_wf_page_status",
        ),
    )
