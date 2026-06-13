"""Tests for BypassService."""

from __future__ import annotations

import pytest

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.application import Application
from app.models.execution_plan import ExecutionPlan
from app.models.project import Project
from app.services.bypass_service import BypassService


class TestBypassService:
    """BypassService unit tests."""

    async def _seed_plan(self, session, suffix: str = "1") -> ExecutionPlan:
        app = Application(
            application_id=f"app-bp-{suffix}",
            application_name=f"BpApp{suffix}",
            local_path=f"/tmp/bp{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-bp-{suffix}",
            project_name=f"BpProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        plan = ExecutionPlan(
            plan_id=f"plan-bp-{suffix}",
            project_id=proj.project_id,
            version="v1.0",
        )
        session.add(plan)
        await session.flush()
        return plan

    @pytest.mark.asyncio
    async def test_apply_bypass(self, db_session) -> None:
        """Should create bypass record with PENDING status."""
        plan = await self._seed_plan(db_session)
        svc = BypassService(db_session)
        record = await svc.apply_bypass(
            gate_id="gate-001",
            plan_id=plan.plan_id,
            stage_id="stage-001",
            skill_id="skill-001",
            triggered_by="user-001",
            reason="Emergency deployment required",
            authorizer_token="token-123",
            deadline_hours=12,
        )
        assert record.status == "PENDING_POST_APPROVAL"
        assert record.reason == "Emergency deployment required"
        assert record.deadline_at is not None

    @pytest.mark.asyncio
    async def test_apply_bypass_reason_too_short(self, db_session) -> None:
        """Should reject reason < 5 chars."""
        plan = await self._seed_plan(db_session, suffix="short")
        svc = BypassService(db_session)
        with pytest.raises(BadRequestError):
            await svc.apply_bypass(
                gate_id="gate-001",
                plan_id=plan.plan_id,
                stage_id="stage-001",
                skill_id="skill-001",
                triggered_by="user-001",
                reason="abc",
                authorizer_token="token-123",
            )

    @pytest.mark.asyncio
    async def test_approve_bypass(self, db_session) -> None:
        """Should update status to CLOSED."""
        plan = await self._seed_plan(db_session, suffix="approve")
        svc = BypassService(db_session)
        record = await svc.apply_bypass(
            gate_id="gate-001",
            plan_id=plan.plan_id,
            stage_id="stage-001",
            skill_id="skill-001",
            triggered_by="user-001",
            reason="Valid reason here",
            authorizer_token="token-123",
        )
        await db_session.flush()

        updated = await svc.approve_bypass(record.record_id, "admin-001")
        assert updated.status == "CLOSED"
        assert updated.closed_at is not None

    @pytest.mark.asyncio
    async def test_approve_bypass_not_found(self, db_session) -> None:
        """Should raise NotFoundError for unknown record."""
        svc = BypassService(db_session)
        with pytest.raises(NotFoundError):
            await svc.approve_bypass("no-such-record", "admin-001")
