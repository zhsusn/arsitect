"""ParallelGroup ORM model."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ParallelGroup(Base):
    """并行组定义表."""

    __tablename__ = "execution_plan_groups"

    group_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.plan_id", ondelete="CASCADE"),
        nullable=False,
    )
    stage_id: Mapped[str] = mapped_column(String(36), nullable=False)
    group_type: Mapped[str] = mapped_column(String(16), nullable=False)
    node_ids: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "group_type IN ('primary_serial', 'auxiliary_parallel')",
            name="ck_group_type",
        ),
    )
