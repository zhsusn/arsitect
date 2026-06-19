"""Template ORM model — four-level project templates."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Template(Base):
    """Project template definition (Trivial / Light / Standard / Deep)."""

    __tablename__ = "templates"

    template_id: Mapped[str] = mapped_column(
        String(16),
        primary_key=True,
    )
    template_name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    stage_count: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_skill_count: Mapped[int] = mapped_column(Integer, nullable=False)
    applicable_complexity: Mapped[str] = mapped_column(String(16), nullable=False)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_execution_strategy: Mapped[str] = mapped_column(
        String(16), nullable=False, default="semi_auto"
    )
    merge_policy_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "template_id IN ('Trivial', 'Light', 'Standard', 'Deep')",
            name="ck_template_id",
        ),
        CheckConstraint(
            "default_execution_strategy IN ('full_auto', 'semi_auto', 'full_manual')",
            name="ck_template_default_execution_strategy",
        ),
    )
