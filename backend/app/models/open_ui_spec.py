"""OpenUISpec ORM model for UI prototype session container."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class OpenUISpec(Base):
    """OpenUI 原型会话表 — 作为 open_ui_pages 的容器."""

    __tablename__ = "open_ui_specs"

    spec_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    spec_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_text: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="提交给 OpenUI 服务的提示词"
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="生成页面数")
    page_titles_json: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="页面标题列表 JSON"
    )
    service_status: Mapped[str] = mapped_column(String(16), nullable=False, default="UNKNOWN")
    generation_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "service_status IN ('UNKNOWN','CHECKING','AVAILABLE','STARTING','UNAVAILABLE','GENERATING','SILENT')",
            name="ck_open_ui_service_status",
        ),
        CheckConstraint(
            "status IN ('DRAFT','GENERATING','GENERATED','RENDERING','FALLBACK','ARCHIVED')",
            name="ck_open_ui_status",
        ),
    )
