"""BypassRecord ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class BypassRecord(Base):
    """旁路审批记录表."""

    __tablename__ = "bypass_records"

    record_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    gate_decision_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("execution_plans.plan_id", ondelete="CASCADE"),
        nullable=False,
    )
    stage_id: Mapped[str] = mapped_column(String(36), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(36), nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(36), nullable=False)
    authorizer_token: Mapped[str] = mapped_column(String(128), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(256), nullable=True, default="紧急执行")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING_POST_APPROVAL")
    deadline_at: Mapped[datetime] = mapped_column(nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING_POST_APPROVAL', 'CLOSED', 'VIOLATION_PENDING')",
            name="ck_bypass_status",
        ),
    )
