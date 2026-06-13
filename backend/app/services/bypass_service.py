"""BypassService — 旁路审批申请与查询."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bypass_record import BypassRecord
from app.models.execution_plan import ExecutionPlan


class BypassService:
    """Handle bypass approval applications."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self._session = session

    async def apply_bypass(
        self,
        gate_id: str,
        plan_id: str,
        stage_id: str,
        skill_id: str,
        triggered_by: str,
        reason: str,
        authorizer_token: str,
        deadline_hours: int = 24,
    ) -> BypassRecord:
        """Apply for a bypass approval.

        Args:
            gate_id: Gate decision identifier.
            plan_id: Execution plan identifier.
            stage_id: Stage identifier.
            skill_id: Skill identifier.
            triggered_by: User ID triggering the bypass.
            reason: Bypass reason (5-500 chars).
            authorizer_token: Authorization token.
            deadline_hours: Hours until bypass expires.

        Returns:
            Created bypass record.
        """
        if len(reason) < 5 or len(reason) > 500:
            from app.core.exceptions import BadRequestError

            raise BadRequestError(detail="Reason must be 5-500 characters")

        record = BypassRecord(
            record_id=f"bypass-{uuid.uuid4()}",
            gate_decision_id=gate_id,
            plan_id=plan_id,
            stage_id=stage_id,
            skill_id=skill_id,
            triggered_by=triggered_by,
            authorizer_token=authorizer_token,
            reason=reason,
            status="PENDING_POST_APPROVAL",
            deadline_at=datetime.now(UTC) + timedelta(hours=deadline_hours),
            created_at=datetime.now(UTC),
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_bypass_applications(self, project_id: str) -> list[BypassRecord]:
        """List bypass applications for a project.

        Args:
            project_id: Project identifier.

        Returns:
            List of bypass records.
        """
        # Join via execution_plans to filter by project
        result = await self._session.execute(
            select(BypassRecord)
            .join(
                ExecutionPlan,
                BypassRecord.plan_id == ExecutionPlan.plan_id,
            )
            .where(ExecutionPlan.project_id == project_id)
            .order_by(BypassRecord.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_for_project(self, project_id: str) -> BypassRecord | None:
        """Get the latest bypass record for a project.

        Args:
            project_id: Project identifier.

        Returns:
            Latest bypass record or None.
        """
        from app.infrastructure.database.repositories.execution_plan_repo import (
            ExecutionPlanRepository,
        )

        plan_repo = ExecutionPlanRepository(self._session)
        plans = await plan_repo.list_by_project(project_id)
        plan_ids = [p.plan_id for p in plans]
        if not plan_ids:
            # Fallback: try matching by plan_id pattern for MVP compatibility
            result = await self._session.execute(
                select(BypassRecord)
                .where(BypassRecord.plan_id.like(f"%{project_id}%"))
                .order_by(BypassRecord.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

        result = await self._session.execute(
            select(BypassRecord)
            .where(BypassRecord.plan_id.in_(plan_ids))
            .order_by(BypassRecord.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_for_gate(self, gate_decision_id: str) -> BypassRecord | None:
        """Get the latest bypass record for a gate decision.

        Args:
            gate_decision_id: Gate decision identifier.

        Returns:
            Latest bypass record or None.
        """
        result = await self._session.execute(
            select(BypassRecord)
            .where(BypassRecord.gate_decision_id == gate_decision_id)
            .order_by(BypassRecord.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def approve_bypass(self, record_id: str, approved_by: str) -> BypassRecord:
        """Approve a bypass application.

        Args:
            record_id: Bypass record identifier.
            approved_by: Approver user ID.

        Returns:
            Updated bypass record.
        """

        result = await self._session.execute(
            select(BypassRecord).where(BypassRecord.record_id == record_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError(detail=f"Bypass record '{record_id}' not found")

        record.status = "CLOSED"
        record.closed_at = datetime.now(UTC)
        await self._session.flush()
        return record
