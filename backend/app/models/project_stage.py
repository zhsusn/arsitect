"""ProjectStage ORM model — runtime stage instance for a project."""

from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Integer, String
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
    skippable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False)
    merge_group_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    execution_status: Mapped[str] = mapped_column(String(16), default="NOT_STARTED")

    __table_args__ = (
        CheckConstraint(
            "status IN ('DEFINED', 'SKIPPED', 'SCHEDULED', 'EXECUTED', 'REMOVED', 'FROZEN', 'ARCHIVED')",
            name="ck_project_stage_status",
        ),
    )
