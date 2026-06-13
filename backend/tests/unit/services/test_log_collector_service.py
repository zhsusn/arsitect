"""Tests for LogCollectorService."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database.repositories.execution_log_repo import (
    ExecutionLogRepository,
)
from app.infrastructure.database.repositories.skill_execution_repo import (
    SkillExecutionRepository,
)
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.skill_execution import SkillExecution
from app.schemas.skill_execution import LogFilterDTO
from app.services.log_collector_service import LogCollectorService


class TestLogCollectorService:
    """LogCollectorService tests."""

    @pytest.mark.asyncio
    async def test_capture_log(self) -> None:
        """capture_log creates a log with auto-generated anchor."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM execution_logs"))
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-lc",
                application_name="LC App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-lc",
                project_name="LC Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            exec_repo = SkillExecutionRepository(session)
            execution = SkillExecution(
                execution_id="exec-1",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
            )
            await exec_repo.create(execution)

            repo = ExecutionLogRepository(session)
            service = LogCollectorService(repo)

            log = await service.capture_log("exec-1", "INFO", "Hello")
            assert log.execution_id == "exec-1"
            assert log.level == "INFO"
            assert log.content == "Hello"
            assert len(log.log_anchor) == 16

    @pytest.mark.asyncio
    async def test_query_logs(self) -> None:
        """query_logs returns logs matching filters."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM execution_logs"))
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-lc2",
                application_name="LC App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-lc2",
                project_name="LC Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            exec_repo = SkillExecutionRepository(session)
            execution = SkillExecution(
                execution_id="exec-2",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
            )
            await exec_repo.create(execution)

            repo = ExecutionLogRepository(session)
            service = LogCollectorService(repo)

            await service.capture_log("exec-2", "INFO", "First log")
            await service.capture_log("exec-2", "ERROR", "Error log")
            await service.capture_log("exec-2", "INFO", "Second log")

            result = await service.query_logs("exec-2", LogFilterDTO())
            assert result.total_count == 3
            assert len(result.log_entries) == 3

    @pytest.mark.asyncio
    async def test_query_logs_with_level_filter(self) -> None:
        """query_logs filters by level."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM execution_logs"))
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-lc3",
                application_name="LC App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-lc3",
                project_name="LC Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            exec_repo = SkillExecutionRepository(session)
            execution = SkillExecution(
                execution_id="exec-3",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
            )
            await exec_repo.create(execution)

            repo = ExecutionLogRepository(session)
            service = LogCollectorService(repo)

            await service.capture_log("exec-3", "INFO", "Info")
            await service.capture_log("exec-3", "ERROR", "Error")

            result = await service.query_logs("exec-3", LogFilterDTO(level="ERROR"))
            assert len(result.log_entries) == 1
            assert result.log_entries[0].level == "ERROR"

    @pytest.mark.asyncio
    async def test_query_logs_with_keyword(self) -> None:
        """query_logs filters by keyword."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM execution_logs"))
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-lc4",
                application_name="LC App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-lc4",
                project_name="LC Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            exec_repo = SkillExecutionRepository(session)
            execution = SkillExecution(
                execution_id="exec-4",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
            )
            await exec_repo.create(execution)

            repo = ExecutionLogRepository(session)
            service = LogCollectorService(repo)

            await service.capture_log("exec-4", "INFO", "Hello world")
            await service.capture_log("exec-4", "INFO", "Goodbye")

            result = await service.query_logs("exec-4", LogFilterDTO(keyword="Hello"))
            assert len(result.log_entries) == 1
            assert result.log_entries[0].content == "Hello world"
