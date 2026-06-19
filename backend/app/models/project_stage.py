"""ProjectStage ORM model — runtime stage instance for a project."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ProjectStage(Base):
    """A stage instance bound to a specific project."""

    __tablename__ = "project_stages"

    project_stage_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    stage_id: Mapped[str] = mapped_column(String(36), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="DEFINED")
    primary_skill_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    auxiliary_skill_ids: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON serialized list
    skippable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False)
    merge_group_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_gate_required: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_advance: Mapped[bool] = mapped_column(Boolean, default=False)
    execution_status: Mapped[str] = mapped_column(String(16), default="NOT_STARTED")
    runtime_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="not_started"
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_strategy: Mapped[str | None] = mapped_column(String(16), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('DEFINED', 'SKIPPED', 'SCHEDULED', 'EXECUTED', 'REMOVED', 'FROZEN', 'ARCHIVED')",
            name="ck_project_stage_status",
        ),
        CheckConstraint(
            "runtime_status IN ('not_started', 'ready', 'in_progress', 'review_pending', 'gate_pending', 'passed', 'blocked', 'skipped')",
            name="ck_project_stage_runtime_status",
        ),
    )
