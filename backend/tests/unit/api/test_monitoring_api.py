"""Tests for MonitoringRouter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.gate_decision import GateDecision
from app.models.operation_log import OperationLog
from app.models.project import Project
from app.models.skill_execution import SkillExecution
from main import app

client = TestClient(app)


class TestMonitoringRouter:
    """Monitoring API tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        """Helper to create an application + project."""
        app = Application(
            application_id=f"app-monapi-{suffix}",
            application_name=f"MonApiApp{suffix}",
            local_path=f"/tmp/monapi{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-monapi-{suffix}",
            project_name=f"MonApiProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
            project_status="Active",
            risk_level="High",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_get_overview(self) -> None:
        """GET /monitoring/overview returns overview data."""
        res = client.get("/api/v1/monitoring/overview")
        assert res.status_code == 200
        data = res.json()
        assert "total_projects" in data
        assert "active_projects" in data

    @pytest.mark.asyncio
    async def test_get_project_stats(self) -> None:
        """GET /monitoring/projects/{id}/stats returns stats."""
        async with AsyncSessionLocal() as session:
            proj = await self._seed_project(session, suffix="stats")
            gate = GateDecision(
                decision_id="g-stats",
                gate_id="g1",
                project_id=proj.project_id,
                gate_type="1",
                status="pending",
            )
            session.add(gate)
            execution = SkillExecution(
                execution_id="exec-stats",
                project_id=proj.project_id,
                stage_id="stage-stats",
                skill_id="skill-stats",
                skill_name="Test",
                overall_status="SUCCESS",
            )
            session.add(execution)
            await session.commit()

        res = client.get(f"/api/v1/monitoring/projects/{proj.project_id}/stats")
        assert res.status_code == 200
        data = res.json()
        assert data["gate_count"] == 1
        assert data["execution_count"] == 1

    @pytest.mark.asyncio
    async def test_list_operation_logs(self) -> None:
        """GET /monitoring/projects/{id}/operation-logs returns logs."""
        async with AsyncSessionLocal() as session:
            proj = await self._seed_project(session, suffix="logs")
            log = OperationLog(
                log_id="log-api-1",
                project_id=proj.project_id,
                action="TEST",
                detail="detail",
            )
            session.add(log)
            await session.commit()

        res = client.get(f"/api/v1/monitoring/projects/{proj.project_id}/operation-logs")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert len(data["logs"]) == 1
        assert data["logs"][0]["action"] == "TEST"
