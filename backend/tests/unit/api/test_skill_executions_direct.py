"""Direct unit tests for skill_executions router (no TestClient)."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.api.v1.skill_executions import (
    _resolve_skill,
    _resolve_stage,
    confirm_release,
    get_execution_logs,
    get_execution_status,
    retry_execution,
)
from app.core.exceptions import BadRequestError, NotFoundError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.project_stage import ProjectStage
from app.models.skill import Skill
from app.models.skill_execution import SkillExecution


class TestSkillExecutionHelpers:
    """Direct tests for internal helpers."""

    @pytest.fixture
    async def seeded(self):
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM skills"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            from app.models.application import Application
            from app.models.project import Project

            app_obj = Application(
                application_id="app-direct",
                application_name="Direct App",
                local_path="/tmp/direct",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-direct",
                project_name="Direct Project",
                application_id="app-direct",
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            stage = ProjectStage(
                project_stage_id="stage-direct",
                project_id="proj-direct",
                stage_id="stage-001",
                order_index=0,
            )
            session.add(stage)

            skill = Skill(
                skill_id="skill-direct",
                skill_name="direct-skill",
                version="1.0.0",
                pattern="generator",
                directory_path="/tmp/direct-skill",
            )
            session.add(skill)
            await session.commit()
            yield session
            # cleanup
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM skills"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

    @pytest.mark.asyncio
    async def test_resolve_skill_none(self, seeded) -> None:
        with pytest.raises(BadRequestError):
            await _resolve_skill(seeded, None)

    @pytest.mark.asyncio
    async def test_resolve_skill_not_found(self, seeded) -> None:
        with pytest.raises(NotFoundError):
            await _resolve_skill(seeded, "no-such-skill")

    @pytest.mark.asyncio
    async def test_resolve_stage_none(self, seeded) -> None:
        with pytest.raises(BadRequestError):
            await _resolve_stage(seeded, None)

    @pytest.mark.asyncio
    async def test_resolve_stage_not_found(self, seeded) -> None:
        with pytest.raises(NotFoundError):
            await _resolve_stage(seeded, "no-such-stage")

    @pytest.mark.asyncio
    async def test_get_execution_status(self, seeded) -> None:
        execution = SkillExecution(
            execution_id="exec-direct",
            project_id="proj-direct",
            stage_id="stage-direct",
            skill_id="skill-direct",
            skill_name="direct-skill",
            current_phase="EXEC",
            phase_status="RUNNING",
            overall_status="RUNNING",
        )
        seeded.add(execution)
        await seeded.commit()

        result = await get_execution_status("exec-direct", db=seeded)
        assert result.execution_id == "exec-direct"

    @pytest.mark.asyncio
    async def test_get_execution_logs(self, seeded) -> None:
        execution = SkillExecution(
            execution_id="exec-log-direct",
            project_id="proj-direct",
            stage_id="stage-direct",
            skill_id="skill-direct",
            skill_name="direct-skill",
        )
        seeded.add(execution)
        await seeded.flush()

        from app.models.execution_log import ExecutionLog

        log = ExecutionLog(
            log_id="log-direct",
            execution_id="exec-log-direct",
            log_anchor="anchor-1",
            level="INFO",
            content="Direct test log",
        )
        seeded.add(log)
        await seeded.commit()

        result = await get_execution_logs("exec-log-direct", db=seeded)
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_retry_execution(self, seeded) -> None:
        execution = SkillExecution(
            execution_id="exec-retry-direct",
            project_id="proj-direct",
            stage_id="stage-direct",
            skill_id="skill-direct",
            skill_name="direct-skill",
            overall_status="FAILED",
            retry_count=0,
        )
        seeded.add(execution)
        await seeded.commit()

        result = await retry_execution("exec-retry-direct", db=seeded)
        assert result.success is True
        assert result.new_execution_id is not None

    @pytest.mark.asyncio
    async def test_confirm_release_not_found(self, seeded) -> None:
        with pytest.raises(NotFoundError):
            await confirm_release("no-such-exec", db=seeded)
