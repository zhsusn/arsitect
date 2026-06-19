"""SizeEstimate ORM model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class SizeEstimate(Base):
    """Size estimate for a project."""

    __tablename__ = "size_estimates"

    estimate_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    module_count: Mapped[int] = mapped_column(Integer, nullable=False)
    interface_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tech_complexity: Mapped[str] = mapped_column(String(16), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    optimistic_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conservative_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    complexity_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint(
            "module_count BETWEEN 1 AND 50",
            name="ck_estimate_module_count",
        ),
        CheckConstraint(
            "interface_count BETWEEN 0 AND 100",
            name="ck_estimate_interface_count",
        ),
        CheckConstraint(
            "page_count BETWEEN 0 AND 50",
            name="ck_estimate_page_count",
        ),
        CheckConstraint(
            "tech_complexity IN ('Low','Medium','High')",
            name="ck_estimate_tech_complexity",
        ),
        CheckConstraint(
            "risk_level IN ('Low','Medium','High')",
            name="ck_estimate_risk_level",
        ),
        CheckConstraint(
            "complexity_level IS NULL OR complexity_level IN ('Trivial','Light','Standard','Deep')",
            name="ck_estimate_complexity_level",
        ),
    )
