"""Stage-level gate controller for project stage gating.

为 StageOrchestrator 提供阶段级 Gate 记录的创建、审批、查询能力，
复用现有 ``gate_decisions`` 表，将 ``gate_id`` 视为 ``project_stage_id``。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.gate_decision import GateDecision


class StageGateController:
    """Manage gate decision records for project stages."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def create_gate(
        self,
        project_stage_id: str,
        project_id: str,
        gate_type: str = "2",
        reason: str | None = None,
    ) -> GateDecision:
        """Create a pending gate decision for a project stage.

        If a pending gate already exists for the stage, return it.

        Args:
            project_stage_id: 项目阶段实例 ID。
            project_id: 所属项目 ID。
            gate_type: Gate 类型（复用现有约束：'1','2','2.5','3','initiation'）。
            reason: 创建原因/摘要。

        Returns:
            GateDecision record.
        """
        stmt = (
            select(GateDecision)
            .where(
                GateDecision.gate_id == project_stage_id,
                GateDecision.status == "pending",
            )
            .order_by(GateDecision.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing

        gate = GateDecision(
            decision_id=str(uuid.uuid4()),
            gate_id=project_stage_id,
            project_id=project_id,
            gate_type=gate_type,
            status="pending",
            reason=reason or "",
            unlocked_stages="[]",
        )
        self._session.add(gate)
        await self._session.flush()
        return gate

    async def decide(
        self,
        project_stage_id: str,
        decision: str,
        operator_id: str = "system",
        reason: str | None = None,
    ) -> GateDecision:
        """Resolve the pending gate for a stage.

        Args:
            project_stage_id: 项目阶段实例 ID。
            decision: 'pass' 或 'reject'。
            operator_id: 审批人 ID。
            reason: 审批意见。

        Returns:
            Updated GateDecision record.

        Raises:
            NotFoundError: If no pending gate exists for the stage.
        """
        stmt = (
            select(GateDecision)
            .where(
                GateDecision.gate_id == project_stage_id,
                GateDecision.status == "pending",
            )
            .order_by(GateDecision.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        gate = result.scalar_one_or_none()
        if gate is None:
            raise NotFoundError(
                detail=f"No pending gate for stage '{project_stage_id}'"
            )

        decision = decision.lower()
        if decision == "pass":
            gate.status = "passed"
        elif decision in ("reject", "rejected"):
            gate.status = "rejected"
        else:
            gate.status = "rejected"

        gate.decision_by = operator_id
        gate.decision_at = datetime.now(UTC)
        created_at = gate.created_at
        now = gate.decision_at
        if created_at is not None and created_at.tzinfo is None:
            now = now.replace(tzinfo=None)
        gate.duration_sec = int(
            ((now - created_at).total_seconds()) if created_at else 0
        )
        if reason:
            gate.reason = reason

        self._session.add(gate)
        await self._session.flush()
        return gate

    async def get_pending_gate(
        self, project_stage_id: str
    ) -> GateDecision | None:
        """Get the latest pending gate decision for a stage."""
        stmt = (
            select(GateDecision)
            .where(
                GateDecision.gate_id == project_stage_id,
                GateDecision.status == "pending",
            )
            .order_by(GateDecision.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: str,
        status: str | None = None,
        limit: int = 100,
    ) -> list[GateDecision]:
        """List gate decisions for a project."""
        stmt = select(GateDecision).where(
            GateDecision.project_id == project_id
        )
        if status:
            stmt = stmt.where(GateDecision.status == status)
        stmt = stmt.order_by(GateDecision.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
