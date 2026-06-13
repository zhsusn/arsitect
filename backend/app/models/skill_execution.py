"""SkillExecution ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class SkillExecution(Base):
    """Skill 执行记录表."""

    __tablename__ = "skill_executions"

    execution_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    stage_id: Mapped[str] = mapped_column(String(36), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(36), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(128), nullable=False)
    trigger_action: Mapped[str] = mapped_column(
        String(16), nullable=False, default="SINGLE_EXECUTE"
    )
    current_phase: Mapped[str] = mapped_column(
        String(16), nullable=False, default="NONE"
    )
    phase_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="RUNNING"
    )
    overall_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="NOT_STARTED"
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    previous_execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("skill_executions.execution_id", ondelete="SET NULL"),
        nullable=True,
    )
    is_release_skill: Mapped[bool] = mapped_column(nullable=False, default=False)
    release_confirmed: Mapped[bool] = mapped_column(nullable=False, default=False)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "trigger_action IN ('SINGLE_EXECUTE', 'BATCH_EXECUTE', 'RETRY')",
            name="ck_exec_trigger_action",
        ),
        CheckConstraint(
            "current_phase IN ('PREP', 'EXEC', 'POST', 'NONE')",
            name="ck_exec_current_phase",
        ),
        CheckConstraint(
            "phase_status IN ('RUNNING', 'COMPLETED', 'FAILED', 'STOPPED')",
            name="ck_exec_phase_status",
        ),
        CheckConstraint(
            "overall_status IN ('NOT_STARTED', 'RUNNING', 'SUCCESS', 'FAILED', 'STOPPED', 'UNKNOWN')",
            name="ck_exec_overall_status",
        ),
        CheckConstraint(
            "retry_count BETWEEN 0 AND 3",
            name="ck_exec_retry_count",
        ),
    )
