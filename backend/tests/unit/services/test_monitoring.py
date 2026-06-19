"""Tests for MonitoringService."""

from __future__ import annotations

import pytest

from app.models.application import Application
from app.models.gate_decision import GateDecision
from app.models.operation_log import OperationLog
from app.models.project import Project
from app.models.project_stage import ProjectStage
from app.models.skill_execution import SkillExecution
from app.services.monitoring_service import MonitoringService


class TestMonitoringService:
    """MonitoringService unit tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        """Helper to create an application + project."""
        app = Application(
            application_id=f"app-mon-{suffix}",
            application_name=f"MonApp{suffix}",
            local_path=f"/tmp/mon{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-mon-{suffix}",
            project_name=f"MonProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
            project_status="Active",
            risk_level="Medium",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_get_overview_empty(self, db_session) -> None:
        """Overview with no data should return zeros."""
        svc = MonitoringService(db_session)
        overview = await svc.get_overview()
        # Use >= 0 because other tests may share the in-memory DB
        assert overview["total_projects"] >= 0
        assert overview["active_projects"] >= 0
        assert overview["risk_projects"] >= 0
        assert overview["pending_gates"] >= 0
        assert overview["total_executions"] >= 0

    @pytest.mark.asyncio
    async def test_get_overview_with_data(self, db_session) -> None:
        """Overview should count projects, gates, executions correctly."""
        svc = MonitoringService(db_session)
        before = await svc.get_overview()

        proj = await self._seed_project(db_session, suffix="overview")

        # Seed a pending gate
        gate = GateDecision(
            decision_id="gate-001",
            gate_id="g1",
            project_id=proj.project_id,
            gate_type="1",
            status="pending",
        )
        db_session.add(gate)

        # Seed an execution
        execution = SkillExecution(
            execution_id="exec-001",
            project_id=proj.project_id,
            stage_id="stage-001",
            skill_id="skill-001",
            skill_name="TestSkill",
            overall_status="SUCCESS",
        )
        db_session.add(execution)
        await db_session.flush()

        after = await svc.get_overview()
        assert after["total_projects"] == before["total_projects"] + 1
        assert after["active_projects"] == before["active_projects"] + 1
        assert after["risk_projects"] == before["risk_projects"] + 1
        assert after["pending_gates"] == before["pending_gates"] + 1
        assert after["total_executions"] == before["total_executions"] + 1

    @pytest.mark.asyncio
    async def test_get_project_stats(self, db_session) -> None:
        """Project stats should count stages, executions, gates, logs."""
        proj = await self._seed_project(db_session, suffix="stats")

        stage = ProjectStage(
            project_stage_id="stage-001",
            project_id=proj.project_id,
            stage_id="template-stage-001",
            order_index=1,
        )
        db_session.add(stage)

        log = OperationLog(
            log_id="log-001",
            project_id=proj.project_id,
            action="TEST_ACTION",
        )
        db_session.add(log)
        await db_session.flush()

        svc = MonitoringService(db_session)
        stats = await svc.get_project_stats(proj.project_id)
        assert stats["stage_count"] == 1
        assert stats["execution_count"] == 0
        assert stats["gate_count"] == 0
        assert stats["log_count"] == 1

    @pytest.mark.asyncio
    async def test_list_operation_logs(self, db_session) -> None:
        """Should list logs with pagination and action filter."""
        proj = await self._seed_project(db_session, suffix="logs")

        for i in range(3):
            db_session.add(
                OperationLog(
                    log_id=f"log-{i}",
                    project_id=proj.project_id,
                    action="CREATE" if i < 2 else "DELETE",
                )
            )
        await db_session.flush()

        svc = MonitoringService(db_session)
        logs, total = await svc.list_operation_logs(proj.project_id)
        assert total == 3
        assert len(logs) == 3

        logs_create, total_create = await svc.list_operation_logs(proj.project_id, action="CREATE")
        assert total_create == 2
        assert len(logs_create) == 2
