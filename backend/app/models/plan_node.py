"""PlanNode ORM model."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class PlanNode(Base):
    """执行计划节点表."""

    __tablename__ = "execution_plan_nodes"

    node_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.plan_id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[str] = mapped_column(String(36), nullable=False)
    stage_id: Mapped[str] = mapped_column(String(36), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    node_type: Mapped[str] = mapped_column(String(16), nullable=False, default="primary")
    module_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="NOT_STARTED")

    __table_args__ = (
        CheckConstraint(
            "node_type IN ('primary', 'auxiliary')",
            name="ck_node_type",
        ),
        CheckConstraint(
            "status IN ('NOT_STARTED', 'READY', 'EXECUTING', 'COMPLETED', 'FAILED', 'CANCELLED', 'BYPASS_EXECUTING')",
            name="ck_node_status",
        ),
    )
