"""ProjectReview ORM model."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ProjectReview(Base):
    """A generic review record for project artifacts and checklist items."""

    __tablename__ = "project_reviews"

    review_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True
    )
    review_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # e.g. 'gate1', 'uat', 'code_review', 'release'
    item_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )  # e.g. story_id, artifact_id, checklist_item_id, review_item_id
    item_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # e.g. 'user-story', 'prd', 'sketch', 'size-estimate', 'acceptance-criteria', 'checklist', 'review-item'
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending"
    )  # e.g. 'pending', 'approved', 'rejected', 'passed', 'failed', 'skipped', 'open', 'fixed', 'waived', 'checked'
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'passed', 'failed', "
            "'skipped', 'open', 'fixed', 'waived', 'checked')",
            name="ck_review_status",
        ),
        CheckConstraint(
            "review_type IN ('gate1', 'uat', 'code_review', 'release')",
            name="ck_review_type",
        ),
    )
