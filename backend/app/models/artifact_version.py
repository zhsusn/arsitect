"""ArtifactVersion ORM model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ArtifactVersion(Base):
    """Artifact version snapshot."""

    __tablename__ = "artifact_versions"

    version_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    artifact_id: Mapped[str] = mapped_column(
        ForeignKey("artifact_files.artifact_id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    operation_type: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        CheckConstraint(
            "operation_type IN ('snapshot', 'rollback')",
            name="ck_artifact_version_operation_type",
        ),
    )
