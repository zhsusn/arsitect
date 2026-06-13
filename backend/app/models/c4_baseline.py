"""C4 Baseline — unified YAML DSL storage per project."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class C4Baseline(Base):
    """Versioned C4 DSL baseline (arsitect.aac.yml format)."""

    __tablename__ = "c4_baselines"

    baseline_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    dsl_content: Mapped[str] = mapped_column(Text, nullable=False)
    dsl_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    level: Mapped[str] = mapped_column(String(10), nullable=False, default="L1-L4")
    is_current: Mapped[bool] = mapped_column(default=True, nullable=False)
    compiled_from: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "level IN ('L1','L2','L3','L4','L1-L4')",
            name="ck_c4_baseline_level",
        ),
    )
