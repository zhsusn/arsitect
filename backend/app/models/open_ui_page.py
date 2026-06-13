"""OpenUIPage ORM model for multi-page prototype storage."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class OpenUIPage(Base):
    """OpenUI 原型页面表 — 存储多页面拆分后的单页 HTML."""

    __tablename__ = "open_ui_pages"

    page_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    spec_id: Mapped[str] = mapped_column(
        ForeignKey("open_ui_specs.spec_id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    container_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="映射的 C4 Container 标识"
    )
    page_title: Mapped[str] = mapped_column(String(128), nullable=False)
    html_content: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="单页 HTML 内容片段"
    )
    page_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="DRAFT"
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
            "status IN ('DRAFT','GENERATED','LOADED','ERROR')",
            name="ck_open_ui_page_status",
        ),
    )
