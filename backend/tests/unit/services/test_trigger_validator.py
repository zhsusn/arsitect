"""Tests for TriggerValidator."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.infrastructure.database.repositories.skill_execution_repo import (
    SkillExecutionRepository,
)
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.skill_execution import SkillExecution
from app.schemas.skill_execution import ExecutionTriggerDTO
from app.services.trigger_validator import TriggerValidator


class TestTriggerValidator:
    """TriggerValidator tests."""

    @pytest.mark.asyncio
    async def test_single_execute_valid_when_no_running(self) -> None:
        """SINGLE_EXECUTE passes when no running execution exists."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            repo = SkillExecutionRepository(session)
            validator = TriggerValidator(repo)

            dto = ExecutionTriggerDTO(
                trigger_action="SINGLE_EXECUTE",
                target_stage_id="stage-1",
                target_skill_name="test-skill",
            )
            result = await validator.validate_trigger(dto, "test-skill", False)
            assert result.valid is True

    @pytest.mark.asyncio
    async def test_single_execute_invalid_when_running(self) -> None:
        """SINGLE_EXECUTE fails when running execution exists."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-1",
                application_name="Test App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-1",
                project_name="Test Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            repo = SkillExecutionRepository(session)
            validator = TriggerValidator(repo)

            execution = SkillExecution(
                execution_id=str(uuid.uuid4()),
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
                trigger_action="SINGLE_EXECUTE",
                overall_status="RUNNING",
            )
            await repo.create(execution)

            dto = ExecutionTriggerDTO(
                trigger_action="SINGLE_EXECUTE",
                target_stage_id="stage-1",
                target_skill_name="test-skill",
            )
            result = await validator.validate_trigger(dto, "test-skill", False)
            assert result.valid is False
            assert result.error_code == "EXECUTION_ALREADY_IN_PROGRESS"

    @pytest.mark.asyncio
    async def test_release_skill_requires_confirmation(self) -> None:
        """Release skill requires confirm_release=True."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            repo = SkillExecutionRepository(session)
            validator = TriggerValidator(repo)

            dto = ExecutionTriggerDTO(
                trigger_action="SINGLE_EXECUTE",
                target_stage_id="stage-1",
                target_skill_name="release-management",
                confirm_release=False,
            )
            result = await validator.validate_trigger(dto, "release-management", True)
            assert result.valid is False
            assert result.error_code == "RELEASE_CONFIRMATION_REQUIRED"

    @pytest.mark.asyncio
    async def test_release_skill_passes_with_confirmation(self) -> None:
        """Release skill passes when confirm_release=True."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            repo = SkillExecutionRepository(session)
            validator = TriggerValidator(repo)

            dto = ExecutionTriggerDTO(
                trigger_action="SINGLE_EXECUTE",
                target_stage_id="stage-1",
                target_skill_name="release-management",
                confirm_release=True,
            )
            result = await validator.validate_trigger(dto, "release-management", True)
            assert result.valid is True

    @pytest.mark.asyncio
    async def test_retry_requires_previous_id(self) -> None:
        """RETRY fails without previous_execution_id."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            repo = SkillExecutionRepository(session)
            validator = TriggerValidator(repo)

            dto = ExecutionTriggerDTO(
                trigger_action="RETRY",
                target_stage_id="stage-1",
                target_skill_name="test-skill",
            )
            result = await validator.validate_trigger(dto, "test-skill", False)
            assert result.valid is False
            assert result.error_code == "PREVIOUS_EXECUTION_REQUIRED"

    @pytest.mark.asyncio
    async def test_retry_fails_when_previous_not_found(self) -> None:
        """RETRY fails when previous execution not found."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            repo = SkillExecutionRepository(session)
            validator = TriggerValidator(repo)

            dto = ExecutionTriggerDTO(
                trigger_action="RETRY",
                target_stage_id="stage-1",
                target_skill_name="test-skill",
                previous_execution_id="nonexistent",
            )
            result = await validator.validate_trigger(dto, "test-skill", False)
            assert result.valid is False
            assert result.error_code == "PREVIOUS_EXECUTION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_retry_fails_when_previous_not_failed(self) -> None:
        """RETRY fails when previous execution is not FAILED."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-2",
                application_name="Test App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-2",
                project_name="Test Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            repo = SkillExecutionRepository(session)
            validator = TriggerValidator(repo)

            execution = SkillExecution(
                execution_id="prev-1",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
                trigger_action="SINGLE_EXECUTE",
                overall_status="SUCCESS",
            )
            await repo.create(execution)

            dto = ExecutionTriggerDTO(
                trigger_action="RETRY",
                target_stage_id="stage-1",
                target_skill_name="test-skill",
                previous_execution_id="prev-1",
            )
            result = await validator.validate_trigger(dto, "test-skill", False)
            assert result.valid is False
            assert result.error_code == "PREVIOUS_EXECUTION_NOT_FAILED"

    @pytest.mark.asyncio
    async def test_retry_fails_when_limit_exceeded(self) -> None:
        """RETRY fails when retry_count >= 3."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-3",
                application_name="Test App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-3",
                project_name="Test Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            repo = SkillExecutionRepository(session)
            validator = TriggerValidator(repo)

            execution = SkillExecution(
                execution_id="prev-2",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
                trigger_action="SINGLE_EXECUTE",
                overall_status="FAILED",
                retry_count=3,
            )
            await repo.create(execution)

            dto = ExecutionTriggerDTO(
                trigger_action="RETRY",
                target_stage_id="stage-1",
                target_skill_name="test-skill",
                previous_execution_id="prev-2",
            )
            result = await validator.validate_trigger(dto, "test-skill", False)
            assert result.valid is False
            assert result.error_code == "RETRY_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_retry_valid(self) -> None:
        """RETRY passes when conditions are met."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-4",
                application_name="Test App",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-4",
                project_name="Test Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            repo = SkillExecutionRepository(session)
            validator = TriggerValidator(repo)

            execution = SkillExecution(
                execution_id="prev-3",
                project_id=proj.project_id,
                stage_id="stage-1",
                skill_id="skill-1",
                skill_name="test-skill",
                trigger_action="SINGLE_EXECUTE",
                overall_status="FAILED",
                retry_count=1,
            )
            await repo.create(execution)

            dto = ExecutionTriggerDTO(
                trigger_action="RETRY",
                target_stage_id="stage-1",
                target_skill_name="test-skill",
                previous_execution_id="prev-3",
            )
            result = await validator.validate_trigger(dto, "test-skill", False)
            assert result.valid is True

    @pytest.mark.asyncio
    async def test_is_release_skill(self) -> None:
        """_is_release_skill returns correct values."""
        async with AsyncSessionLocal() as session:
            repo = SkillExecutionRepository(session)
            validator = TriggerValidator(repo)

            assert validator._is_release_skill("release-management") is True
            assert validator._is_release_skill("finish") is True
            assert validator._is_release_skill("git-automation") is True
            assert validator._is_release_skill("other-skill") is False
