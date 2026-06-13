"""Tests for StatusAggregator."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.exceptions import NotFoundError
from app.infrastructure.database.repositories.skill_execution_repo import (
    SkillExecutionRepository,
)
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.skill_execution import SkillExecution
from app.services.status_aggregator import StatusAggregator


class TestStatusAggregator:
    """StatusAggregator tests."""

    @pytest.mark.asyncio
    async def test_poll_execution_status(self) -> None:
        """poll_execution_status returns correct DTO."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-sa",
                application_name="SA App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-sa",
                project_name="SA Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            repo = SkillExecutionRepository(session)
            execution = SkillExecution(
                execution_id="exec-1",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
                current_phase="EXEC",
                phase_status="RUNNING",
                overall_status="RUNNING",
            )
            await repo.create(execution)

            aggregator = StatusAggregator(repo)
            result = await aggregator.poll_execution_status("exec-1")

            assert result.execution_id == "exec-1"
            assert result.current_phase == "EXEC"
            assert result.phase_status == "RUNNING"
            assert result.overall_status == "RUNNING"
            assert result.stage_progress_percent == 66

    @pytest.mark.asyncio
    async def test_poll_execution_status_not_found(self) -> None:
        """poll_execution_status raises NotFoundError for missing execution."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.commit()

            repo = SkillExecutionRepository(session)
            aggregator = StatusAggregator(repo)

            with pytest.raises(NotFoundError):
                await aggregator.poll_execution_status("nonexistent")

    @pytest.mark.asyncio
    async def test_calculate_stage_progress(self) -> None:
        """calculate_stage_progress maps phases correctly."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-sa2",
                application_name="SA App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-sa2",
                project_name="SA Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            repo = SkillExecutionRepository(session)
            execution = SkillExecution(
                execution_id="exec-2",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
                current_phase="POST",
                overall_status="RUNNING",
            )
            await repo.create(execution)

            aggregator = StatusAggregator(repo)
            result = await aggregator.calculate_stage_progress("exec-2")

            assert result.execution_id == "exec-2"
            assert result.stage_progress_percent == 90

    @pytest.mark.asyncio
    async def test_calculate_stage_progress_not_found(self) -> None:
        """calculate_stage_progress raises NotFoundError for missing execution."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.commit()

            repo = SkillExecutionRepository(session)
            aggregator = StatusAggregator(repo)

            with pytest.raises(NotFoundError):
                await aggregator.calculate_stage_progress("nonexistent")
