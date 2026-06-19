"""StageRollbackLog ORM model — audit trail for stage rollbacks."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class StageRollbackLog(Base):
    """Audit trail for stage rollback operations."""

    __tablename__ = "stage_rollback_logs"

    log_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    from_stage_id: Mapped[str] = mapped_column(String(36), nullable=False)
    to_stage_id: Mapped[str] = mapped_column(String(36), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    stale_artifact_ids: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON serialized list
    git_snapshot_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    operator_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (
        Index("ix_stage_rollback_logs_project", "project_id"),
    )
