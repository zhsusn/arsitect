"""Tests for RetryManager."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database.repositories.skill_execution_repo import (
    SkillExecutionRepository,
)
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.skill_execution import SkillExecution
from app.services.retry_manager import RetryManager


class TestRetryManager:
    """RetryManager tests."""

    @pytest.mark.asyncio
    async def test_attempt_retry_success(self) -> None:
        """attempt_retry creates a new execution on failure."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-rm",
                application_name="RM App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-rm",
                project_name="RM Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            repo = SkillExecutionRepository(session)
            manager = RetryManager(repo)

            original = SkillExecution(
                execution_id="orig-1",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
                overall_status="FAILED",
                retry_count=1,
            )
            await repo.create(original)

            result = await manager.attempt_retry("orig-1")
            assert result.success is True
            assert result.new_execution_id is not None

            new_exec = await repo.get_by_id(result.new_execution_id)
            assert new_exec is not None
            assert new_exec.trigger_action == "RETRY"
            assert new_exec.previous_execution_id == "orig-1"
            assert new_exec.retry_count == 2

    @pytest.mark.asyncio
    async def test_attempt_retry_not_found(self) -> None:
        """attempt_retry fails when execution not found."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.commit()

            repo = SkillExecutionRepository(session)
            manager = RetryManager(repo)

            result = await manager.attempt_retry("nonexistent")
            assert result.success is False

    @pytest.mark.asyncio
    async def test_attempt_retry_not_failed(self) -> None:
        """attempt_retry fails when execution is not FAILED."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-rm2",
                application_name="RM App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-rm2",
                project_name="RM Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            repo = SkillExecutionRepository(session)
            manager = RetryManager(repo)

            execution = SkillExecution(
                execution_id="orig-2",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
                overall_status="SUCCESS",
            )
            await repo.create(execution)

            result = await manager.attempt_retry("orig-2")
            assert result.success is False

    @pytest.mark.asyncio
    async def test_attempt_retry_limit_exceeded(self) -> None:
        """attempt_retry fails when retry_count >= 3."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-rm3",
                application_name="RM App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-rm3",
                project_name="RM Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            repo = SkillExecutionRepository(session)
            manager = RetryManager(repo)

            execution = SkillExecution(
                execution_id="orig-3",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
                overall_status="FAILED",
                retry_count=3,
            )
            await repo.create(execution)

            result = await manager.attempt_retry("orig-3")
            assert result.success is False
