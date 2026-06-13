"""TemplateStage ORM model — stages within a template."""

from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class TemplateStage(Base):
    """A stage definition belonging to a template."""

    __tablename__ = "template_stages"

    stage_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    stage_name: Mapped[str] = mapped_column(String(64), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    template_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("templates.template_id"),
        nullable=False,
    )
    primary_skill_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    auxiliary_skill_ids: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON serialized list
    gate_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    skippable: Mapped[bool] = mapped_column(Boolean, default=False)
    merge_group_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_present_in: Mapped[str] = mapped_column(
        String(16),
        default="Standard",
    )

    __table_args__ = (
        CheckConstraint(
            "is_present_in IN ('Trivial', 'Light', 'Standard', 'Deep')",
            name="ck_stage_present_in",
        ),
    )
