"""ExecutionIssue ORM model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ExecutionIssueType(StrEnum):
    """Execution issue types."""

    COMPILE_ERROR = "compile_error"
    TEST_FAILURE = "test_failure"
    ARCH_MISMATCH = "arch_mismatch"
    INTERFACE_MISMATCH = "interface_mismatch"
    OTHER = "other"


class ExecutionIssueStatus(StrEnum):
    """Execution issue lifecycle states."""

    OPEN = "open"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ExecutionIssue(Base):
    """Execution issue entity representing a problem found during execution."""

    __tablename__ = "execution_issues"

    issue_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[str | None] = mapped_column(
        ForeignKey("execution_tasks.task_id", ondelete="SET NULL"), nullable=True
    )
    issue_type: Mapped[str] = mapped_column(String(16), nullable=False)
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_artifacts: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_to_architecture: Mapped[bool] = mapped_column(default=False)
    target_artifact_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    change_request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "issue_type IN ('compile_error', 'test_failure', 'arch_mismatch', 'interface_mismatch', 'other')",
            name="ck_execution_issue_type",
        ),
        CheckConstraint(
            "status IN ('open', 'resolved', 'closed')",
            name="ck_execution_issue_status",
        ),
    )
