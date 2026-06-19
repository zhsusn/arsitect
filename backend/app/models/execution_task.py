"""ExecutionTask ORM model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ExecutionTaskType(StrEnum):
    """Execution task types."""

    CODING = "coding"
    TEST = "test"
    BUGFIX = "bugfix"


class ExecutionTaskStatus(StrEnum):
    """Execution task lifecycle states."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ExecutionTask(Base):
    """Execution task entity representing a runnable unit in the task center."""

    __tablename__ = "execution_tasks"

    task_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="skill")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    input_artifacts: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    assigned_skill_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    parent_module: Mapped[str | None] = mapped_column(String(64), nullable=True)
    output_artifact_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('coding', 'test', 'bugfix')",
            name="ck_execution_task_type",
        ),
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'passed', 'failed', 'blocked')",
            name="ck_execution_task_status",
        ),
        CheckConstraint(
            "retry_count BETWEEN 0 AND 3",
            name="ck_execution_task_retry_count",
        ),
    )
