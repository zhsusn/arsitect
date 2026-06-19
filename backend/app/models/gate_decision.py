"""GateDecision ORM model."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class GateDecision(Base):
    """A gate decision record for project stage gating."""

    __tablename__ = "gate_decisions"

    decision_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    gate_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    gate_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    decision_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    decision_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    unlocked_stages: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'passed', 'rejected', 'bypassed')",
            name="ck_gate_status",
        ),
        CheckConstraint(
            "gate_type IN ('1', '2', '2.5', '3', 'initiation')",
            name="ck_gate_type",
        ),
    )

    def set_unlocked_stages(self, stages: list[str]) -> None:
        """Serialize unlocked stages to JSON string."""
        self.unlocked_stages = json.dumps(stages)

    def get_unlocked_stages(self) -> list[str]:
        """Deserialize unlocked stages from JSON string."""
        result: list[str] = json.loads(self.unlocked_stages)
        return result
