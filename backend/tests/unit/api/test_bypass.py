"""Tests for BypassRouter.

Covers DR-017 HITL Bypass Approval API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.v1.bypass import approve_bypass, list_bypass_applications
from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.bypass_record import BypassRecord
from app.models.gate_decision import GateDecision
from app.models.project import Project
from app.schemas.bypass import BypassApproveDTO
from main import app

client = TestClient(app)


class TestBypassRouter:
    """Bypass router API tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM bypass_records"))
            await session.execute(text("DELETE FROM gate_decisions"))
            await session.execute(text("DELETE FROM execution_plans"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-bypass-router",
                application_name="Bypass Router App",
                local_path="/tmp/bypass-router",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-bypass-router",
                project_name="Bypass Router Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            # Seed execution_plan to satisfy FK constraint on bypass_records.plan_id
            from app.models.execution_plan import ExecutionPlan
            plan = ExecutionPlan(
                plan_id=f"plan-{proj.project_id}",
                project_id=proj.project_id,
                version="1.0.0",
                is_frozen=False,
                template_level="Standard",
            )
            session.add(plan)
            await session.flush()

            gate = GateDecision(
                decision_id="gate-1",
                gate_id="gate-1",
                project_id=proj.project_id,
                gate_type="1",
                status="pending",
            )
            session.add(gate)
            await session.commit()
            return proj

    @pytest.fixture
    async def seeded_record(self, seeded_project: Project) -> BypassRecord:
        """Seed a bypass record."""
        async with AsyncSessionLocal() as session:
            from datetime import datetime
            record = BypassRecord(
                record_id="bypass-test-001",
                plan_id=f"plan-{seeded_project.project_id}",
                stage_id="stage-1",
                skill_id="skill-1",
                triggered_by="user-1",
                authorizer_token="x" * 32,
                reason="Production hotfix required",
                status="PENDING_POST_APPROVAL",
                deadline_at=datetime(2026, 12, 31, 0, 0, 0),
            )
            session.add(record)
            await session.commit()
            return record

    @pytest.mark.asyncio
    async def test_apply_bypass(self, seeded_project: Project) -> None:
        """TEST-0401: POST applies for bypass on a gate."""
        payload = {
            "plan_id": f"plan-{seeded_project.project_id}",
            "stage_id": "stage-1",
            "skill_id": "skill-1",
            "triggered_by": "user-1",
            "reason": "Production hotfix required",
            "authorizer_token": "x" * 32,
            "deadline_hours": 24,
        }
        res = client.post("/api/v1/gates/gate-1/bypass", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "PENDING_POST_APPROVAL"
        assert data["reason"] == "Production hotfix required"

    @pytest.mark.asyncio
    async def test_apply_bypass_reason_too_short(self, seeded_project: Project) -> None:
        """TEST-0402: POST with short reason returns 422."""
        payload = {
            "plan_id": f"plan-{seeded_project.project_id}",
            "stage_id": "stage-1",
            "skill_id": "skill-1",
            "triggered_by": "user-1",
            "reason": "x",
            "authorizer_token": "x" * 32,
        }
        res = client.post("/api/v1/gates/gate-1/bypass", json=payload)
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_list_bypass_applications(self, seeded_project: Project, seeded_record: BypassRecord) -> None:
        """TEST-0403: GET lists bypass applications (Direct)."""
        async with AsyncSessionLocal() as session:
            result = await list_bypass_applications(seeded_project.project_id, db=session)
            assert isinstance(result, list)
            assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_approve_bypass(self, seeded_record: BypassRecord) -> None:
        """TEST-0404: POST approves a bypass application (Direct)."""
        async with AsyncSessionLocal() as session:
            dto = BypassApproveDTO(approved_by="admin-1")
            result = await approve_bypass("bypass-test-001", dto, db=session)
            assert result.status == "CLOSED"

    @pytest.mark.asyncio
    async def test_approve_bypass_not_found(self, seeded_project: Project) -> None:
        """TEST-0405: POST approve on nonexistent record returns 404 (Direct)."""
        async with AsyncSessionLocal() as session:
            dto = BypassApproveDTO(approved_by="admin-1")
            with pytest.raises(NotFoundError):
                await approve_bypass("no-such-record", dto, db=session)
