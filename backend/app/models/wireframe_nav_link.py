"""WireframeNavLink ORM model for page-to-page navigation relationships."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class WireframeNavLink(Base):
    """页面跳转关系表 — NavigationLinker 输出."""

    __tablename__ = "wireframe_nav_links"

    link_id: Mapped[str] = mapped_column(
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
    source_page_id: Mapped[str] = mapped_column(
        ForeignKey("wireframe_pages.page_id", ondelete="CASCADE"),
        nullable=False,
    )
    target_page_id: Mapped[str] = mapped_column(
        ForeignKey("wireframe_pages.page_id", ondelete="CASCADE"),
        nullable=False,
    )
    interface_refs_json: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="关联 C4 接口列表 JSON"
    )
    relation_strength: Mapped[str] = mapped_column(String(8), nullable=False, default="weak")
    interface_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_marked_missing: Mapped[bool] = mapped_column(
        default=False, comment="是否被用户标记为缺失接口"
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "relation_strength IN ('weak','strong')",
            name="ck_nav_link_strength",
        ),
    )
