"""Project ORM model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ProjectState(StrEnum):
    """Project lifecycle states."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class Project(Base):
    """Project entity representing a managed SDLC project."""

    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_name: Mapped[str] = mapped_column(String(64), nullable=False)
    project_description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    project_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="Draft"
    )
    application_id: Mapped[str] = mapped_column(
        ForeignKey("applications.application_id"), nullable=False
    )
    template_level: Mapped[str] = mapped_column(String(16), nullable=False)
    progress_percent: Mapped[int] = mapped_column(
        nullable=False, default=0
    )
    current_stage: Mapped[str | None] = mapped_column(String(32), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, default="None")
    last_activity_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_activity_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    size_estimate_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "project_status IN ('Draft','Active','Archived','Cancelled')",
            name="ck_project_status",
        ),
        CheckConstraint(
            "template_level IN ('Trivial','Light','Standard','Deep')",
            name="ck_project_template_level",
        ),
        CheckConstraint(
            "progress_percent BETWEEN 0 AND 100",
            name="ck_project_progress",
        ),
        CheckConstraint(
            "risk_level IN ('None','Low','Medium','High')",
            name="ck_project_risk_level",
        ),
    )
