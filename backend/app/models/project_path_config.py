"""ProjectPathConfig ORM model — persisted complexity route decision."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ProjectPathConfig(Base):
    """Persisted complexity route and execution strategy for a project."""

    __tablename__ = "project_path_config"

    config_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    template_level: Mapped[str] = mapped_column(String(16), nullable=False)
    execution_strategy: Mapped[str] = mapped_column(String(16), nullable=False)
    merge_policy_json: Mapped[str] = mapped_column(Text, nullable=False)
    selected_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )
    selected_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "template_level IN ('Trivial', 'Light', 'Standard', 'Deep')",
            name="ck_project_path_config_template_level",
        ),
        CheckConstraint(
            "execution_strategy IN ('full_auto', 'semi_auto', 'full_manual')",
            name="ck_project_path_config_execution_strategy",
        ),
        Index("ix_project_path_config_project", "project_id"),
    )
