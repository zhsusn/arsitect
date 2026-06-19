"""StageSkillBinding ORM model — skill binding snapshot for a project stage."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class StageSkillBinding(Base):
    """Skill binding snapshot for a project stage.

    Records which skills are bound to a project stage at creation time,
    including primary/auxiliary role, execution order and optional config.
    """

    __tablename__ = "stage_skill_bindings"

    binding_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_stage_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("project_stages.project_stage_id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default="primary"
    )
    execution_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    config_snapshot: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON serialized dict
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('primary', 'auxiliary')",
            name="ck_stage_skill_binding_role",
        ),
        Index("ix_stage_skill_bindings_stage", "project_stage_id"),
        Index("ix_stage_skill_bindings_skill", "skill_id"),
    )
