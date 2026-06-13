"""ExecutionPlan ORM model."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin


class ExecutionPlan(Base, TimestampMixin):
    """执行计划主表."""

    __tablename__ = "execution_plans"

    plan_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(16), nullable=False, default="v1.0")
    is_frozen: Mapped[bool] = mapped_column(nullable=False, default=False)
    template_level: Mapped[str | None] = mapped_column(String(16), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "template_level IS NULL OR template_level IN ('Trivial','Light','Standard','Deep')",
            name="ck_plan_template_level",
        ),
    )
