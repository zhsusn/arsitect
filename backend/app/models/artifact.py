"""ArtifactFile ORM model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ArtifactFile(Base):
    """Artifact file entity representing a managed SDLC artifact."""

    __tablename__ = "artifact_files"

    artifact_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    stage_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    skill_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("skill_executions.execution_id", ondelete="SET NULL"),
        nullable=True,
    )
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str] = mapped_column(String(4096), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(default=0)
    current_version: Mapped[int] = mapped_column(default=1)
    external_status: Mapped[str] = mapped_column(String(16), default="normal")
    last_synced_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(nullable=True)
    stale_flag: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "file_type IN ('md', 'yaml', 'json', 'mermaid', 'openapi', 'txt', 'other')",
            name="ck_artifact_file_type",
        ),
        CheckConstraint(
            "external_status IN ('normal', 'modified', 'deleted')",
            name="ck_artifact_external_status",
        ),
    )
