"""Tests for SkillExecutionsRouter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.exceptions import BadRequestError, NotFoundError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.project_stage import ProjectStage
from app.models.skill import Skill
from app.models.skill_execution import SkillExecution
from main import app

client = TestClient(app)


class TestSkillExecutionsRouter:
    """SkillExecutionsRouter tests."""

    @pytest.fixture
    async def seeded_base(self):
        """Seed application, project, project stage, and skill."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM execution_logs"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM skills"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-se",
                application_name="SE App",
                local_path="/tmp/se",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-se",
                project_name="SE Project",
                application_id="app-se",
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            stage = ProjectStage(
                project_stage_id="stage-se",
                project_id="proj-se",
                stage_id="stage-001",
                order_index=0,
            )
            session.add(stage)
            await session.flush()

            skill = Skill(
                skill_id="skill-se",
                skill_name="test-skill",
                version="1.0.0",
                pattern="generator",
                directory_path="/tmp/test-skill",
            )
            session.add(skill)
            await session.commit()

            yield {
                "application": app_obj,
                "project": proj,
                "stage": stage,
                "skill": skill,
            }

            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM execution_logs"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM skills"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

    @pytest.mark.asyncio
    async def test_trigger_execution(self, seeded_base) -> None:
        """POST /executions/trigger creates a new execution."""
        payload = {
            "trigger_action": "SINGLE_EXECUTE",
            "target_stage_id": "stage-se",
            "target_skill_name": "test-skill",
        }
        response = client.post("/api/v1/executions/trigger", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == "proj-se"
        assert data["stage_id"] == "stage-se"
        assert data["skill_name"] == "test-skill"
        assert data["trigger_action"] == "SINGLE_EXECUTE"
        assert data["overall_status"] == "NOT_STARTED"

    @pytest.mark.asyncio
    async def test_trigger_execution_release_requires_confirm(self, seeded_base) -> None:
        """Release skill returns 400 without confirm_release."""
        async with AsyncSessionLocal() as session:
            skill = Skill(
                skill_id="skill-rel",
                skill_name="release-management",
                version="1.0.0",
                pattern="pipeline",
                directory_path="/tmp/rel",
            )
            session.add(skill)
            await session.commit()

        payload = {
            "trigger_action": "SINGLE_EXECUTE",
            "target_stage_id": "stage-se",
            "target_skill_name": "release-management",
            "confirm_release": False,
        }
        response = client.post("/api/v1/executions/trigger", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_trigger_execution_conflict_when_running(self, seeded_base) -> None:
        """Trigger returns 409 when execution already in progress."""
        async with AsyncSessionLocal() as session:
            execution = SkillExecution(
                execution_id="exec-run",
                project_id="proj-se",
                stage_id="stage-se",
                skill_id="skill-se",
                skill_name="test-skill",
                trigger_action="SINGLE_EXECUTE",
                overall_status="RUNNING",
            )
            session.add(execution)
            await session.commit()

        payload = {
            "trigger_action": "SINGLE_EXECUTE",
            "target_stage_id": "stage-se",
            "target_skill_name": "test-skill",
        }
        response = client.post("/api/v1/executions/trigger", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_execution_status(self, seeded_base) -> None:
        """GET /executions/{id}/status returns status."""
        async with AsyncSessionLocal() as session:
            execution = SkillExecution(
                execution_id="exec-stat",
                project_id="proj-se",
                stage_id="stage-se",
                skill_id="skill-se",
                skill_name="test-skill",
                current_phase="EXEC",
                phase_status="RUNNING",
                overall_status="RUNNING",
            )
            session.add(execution)
            await session.commit()

        response = client.get("/api/v1/executions/exec-stat/status")
        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == "exec-stat"
        assert data["current_phase"] == "EXEC"
        assert data["stage_progress_percent"] == 66

    @pytest.mark.asyncio
    async def test_get_execution_status_not_found(self, seeded_base) -> None:
        """GET /executions/{id}/status returns 404 for missing execution."""
        response = client.get("/api/v1/executions/nonexistent/status")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_execution_logs(self, seeded_base) -> None:
        """GET /executions/{id}/logs returns logs."""
        async with AsyncSessionLocal() as session:
            from app.models.execution_log import ExecutionLog

            execution = SkillExecution(
                execution_id="exec-log",
                project_id="proj-se",
                stage_id="stage-se",
                skill_id="skill-se",
                skill_name="test-skill",
            )
            session.add(execution)
            await session.flush()

            log = ExecutionLog(
                log_id="log-1",
                execution_id="exec-log",
                log_anchor="anchor-1",
                level="INFO",
                content="Test log",
            )
            session.add(log)
            await session.commit()

        response = client.get("/api/v1/executions/exec-log/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["log_entries"]) == 1
        assert data["log_entries"][0]["content"] == "Test log"

    @pytest.mark.asyncio
    async def test_get_execution_logs_with_filters(self, seeded_base) -> None:
        """GET /executions/{id}/logs supports filters."""
        async with AsyncSessionLocal() as session:
            from app.models.execution_log import ExecutionLog

            execution = SkillExecution(
                execution_id="exec-log2",
                project_id="proj-se",
                stage_id="stage-se",
                skill_id="skill-se",
                skill_name="test-skill",
            )
            session.add(execution)
            await session.flush()

            session.add_all(
                [
                    ExecutionLog(
                        log_id="log-2",
                        execution_id="exec-log2",
                        log_anchor="anchor-2",
                        level="INFO",
                        content="Info message",
                    ),
                    ExecutionLog(
                        log_id="log-3",
                        execution_id="exec-log2",
                        log_anchor="anchor-3",
                        level="ERROR",
                        content="Error message",
                    ),
                ]
            )
            await session.commit()

        response = client.get("/api/v1/executions/exec-log2/logs?level=ERROR&keyword=Error")
        assert response.status_code == 200
        data = response.json()
        assert len(data["log_entries"]) == 1
        assert data["log_entries"][0]["level"] == "ERROR"

    @pytest.mark.asyncio
    async def test_retry_execution(self, seeded_base) -> None:
        """POST /executions/{id}/retry creates a retry execution."""
        async with AsyncSessionLocal() as session:
            execution = SkillExecution(
                execution_id="exec-retry",
                project_id="proj-se",
                stage_id="stage-se",
                skill_id="skill-se",
                skill_name="test-skill",
                overall_status="FAILED",
                retry_count=0,
            )
            session.add(execution)
            await session.commit()

        response = client.post("/api/v1/executions/exec-retry/retry")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_execution_id"] is not None

    @pytest.mark.asyncio
    async def test_retry_execution_limit_exceeded(self, seeded_base) -> None:
        """POST /executions/{id}/retry returns 200 with success=False when limit exceeded."""
        async with AsyncSessionLocal() as session:
            execution = SkillExecution(
                execution_id="exec-retry2",
                project_id="proj-se",
                stage_id="stage-se",
                skill_id="skill-se",
                skill_name="test-skill",
                overall_status="FAILED",
                retry_count=3,
            )
            session.add(execution)
            await session.commit()

        response = client.post("/api/v1/executions/exec-retry2/retry")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_confirm_release(self, seeded_base) -> None:
        """POST /executions/{id}/confirm-release updates release_confirmed."""
        async with AsyncSessionLocal() as session:
            execution = SkillExecution(
                execution_id="exec-conf",
                project_id="proj-se",
                stage_id="stage-se",
                skill_id="skill-se",
                skill_name="test-skill",
                release_confirmed=False,
            )
            session.add(execution)
            await session.commit()

        response = client.post("/api/v1/executions/exec-conf/confirm-release")
        assert response.status_code == 200
        data = response.json()
        assert data["release_confirmed"] is True

    @pytest.mark.asyncio
    async def test_confirm_release_not_found(self, seeded_base) -> None:
        """POST /executions/{id}/confirm-release returns 404 for missing execution."""
        response = client.post("/api/v1/executions/nonexistent/confirm-release")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_trigger_missing_skill_name(self, seeded_base) -> None:
        """POST /executions/trigger returns 400 when skill name is missing."""
        payload = {
            "trigger_action": "SINGLE_EXECUTE",
            "target_stage_id": "stage-se",
            "target_skill_name": None,
        }
        response = client.post("/api/v1/executions/trigger", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_trigger_skill_not_found(self, seeded_base) -> None:
        """POST /executions/trigger returns 404 when skill does not exist."""
        payload = {
            "trigger_action": "SINGLE_EXECUTE",
            "target_stage_id": "stage-se",
            "target_skill_name": "no-such-skill",
        }
        response = client.post("/api/v1/executions/trigger", json=payload)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_trigger_missing_stage_id(self, seeded_base) -> None:
        """POST /executions/trigger returns 422 when stage id is missing (Pydantic validation)."""
        payload = {
            "trigger_action": "SINGLE_EXECUTE",
            "target_skill_name": "test-skill",
        }
        response = client.post("/api/v1/executions/trigger", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_trigger_stage_not_found(self, seeded_base) -> None:
        """POST /executions/trigger returns 404 when stage does not exist."""
        payload = {
            "trigger_action": "SINGLE_EXECUTE",
            "target_stage_id": "no-such-stage",
            "target_skill_name": "test-skill",
        }
        response = client.post("/api/v1/executions/trigger", json=payload)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_trigger_retry_limit_exceeded(self, seeded_base) -> None:
        """POST /executions/trigger returns 409 when retry limit exceeded."""
        async with AsyncSessionLocal() as session:
            execution = SkillExecution(
                execution_id="exec-limit",
                project_id="proj-se",
                stage_id="stage-se",
                skill_id="skill-se",
                skill_name="test-skill",
                overall_status="FAILED",
                retry_count=3,
            )
            session.add(execution)
            await session.commit()

        payload = {
            "trigger_action": "RETRY",
            "target_stage_id": "stage-se",
            "target_skill_name": "test-skill",
            "previous_execution_id": "exec-limit",
        }
        response = client.post("/api/v1/executions/trigger", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_resolve_helpers_directly(self, seeded_base) -> None:
        """Test internal helper edge cases for coverage."""
        from app.api.v1.skill_executions import _resolve_skill, _resolve_stage

        async with AsyncSessionLocal() as session:
            with pytest.raises(BadRequestError):
                await _resolve_skill(session, None)
            with pytest.raises(NotFoundError):
                await _resolve_skill(session, "no-such-skill")
            with pytest.raises(BadRequestError):
                await _resolve_stage(session, None)
            with pytest.raises(NotFoundError):
                await _resolve_stage(session, "no-such-stage")

    @pytest.mark.asyncio
    async def test_sse_endpoint(self, seeded_base) -> None:
        """GET /advanced/events/{project_id} route is registered for project-level SSE."""
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/v1/advanced/events/{project_id}" in routes
