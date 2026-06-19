"""Tests for SkillExecutionRepository.

Covers DR-008 Skill Executor detailed requirements.
"""

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


class TestSkillExecutionRepository:
    """SkillExecutionRepository unit tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM execution_plans"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-exec-repo",
                application_name="Exec Repo App",
                local_path="/tmp/exec-repo",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-exec-repo",
                project_name="Exec Repo Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.fixture
    async def seeded_executions(self, seeded_project: Project) -> list[SkillExecution]:
        """Seed sample skill executions."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_executions"))
            await session.commit()

            executions = [
                SkillExecution(
                    execution_id="exec-001",
                    project_id=seeded_project.project_id,
                    stage_id="stage-1",
                    skill_id="skill-1",
                    skill_name="requirement-analysis",
                    overall_status="SUCCESS",
                ),
                SkillExecution(
                    execution_id="exec-002",
                    project_id=seeded_project.project_id,
                    stage_id="stage-2",
                    skill_id="skill-2",
                    skill_name="high-level-design",
                    overall_status="RUNNING",
                    current_phase="EXEC",
                ),
                SkillExecution(
                    execution_id="exec-003",
                    project_id=seeded_project.project_id,
                    stage_id="stage-1",
                    skill_id="skill-3",
                    skill_name="detailed-requirements",
                    overall_status="FAILED",
                    retry_count=1,
                ),
            ]
            for e in executions:
                session.add(e)
            await session.commit()
            return executions

    @pytest.mark.asyncio
    async def test_create(self, seeded_project: Project) -> None:
        """TEST-0801: Create a skill execution record.

        Covers AC-F-001: Execution trigger persistence.
        """
        async with AsyncSessionLocal() as session:
            repo = SkillExecutionRepository(session)
            execution = SkillExecution(
                execution_id="exec-new",
                project_id=seeded_project.project_id,
                stage_id="stage-1",
                skill_id="skill-new",
                skill_name="new-skill",
            )
            created = await repo.create(execution)
            assert created.execution_id == "exec-new"
            assert created.overall_status == "NOT_STARTED"

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, seeded_executions: list[SkillExecution]) -> None:
        """TEST-0802: Get execution by existing ID.

        Covers AC-F-007: Execution log retrieval.
        """
        async with AsyncSessionLocal() as session:
            repo = SkillExecutionRepository(session)
            fetched = await repo.get_by_id("exec-001")
            assert fetched is not None
            assert fetched.skill_name == "requirement-analysis"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, seeded_executions: list[SkillExecution]) -> None:
        """TEST-0803: Get execution by nonexistent ID returns None.

        Covers edge case: missing execution lookup.
        """
        async with AsyncSessionLocal() as session:
            repo = SkillExecutionRepository(session)
            fetched = await repo.get_by_id("no-such-exec")
            assert fetched is None

    @pytest.mark.asyncio
    async def test_list_by_project(self, seeded_executions: list[SkillExecution]) -> None:
        """TEST-0804: List executions by project ordered by created_at desc.

        Covers AC-F-007: Project-scoped execution list.
        """
        async with AsyncSessionLocal() as session:
            repo = SkillExecutionRepository(session)
            items = await repo.list_by_project("proj-exec-repo")
            assert len(items) == 3
            # Verify descending order
            assert items[0].created_at >= items[1].created_at

    @pytest.mark.asyncio
    async def test_list_by_stage(self, seeded_executions: list[SkillExecution]) -> None:
        """TEST-0805: List executions by stage.

        Covers AC-F-010: Stage-scoped execution isolation.
        """
        async with AsyncSessionLocal() as session:
            repo = SkillExecutionRepository(session)
            items = await repo.list_by_stage("stage-1")
            assert len(items) == 2
            assert all(e.stage_id == "stage-1" for e in items)

    @pytest.mark.asyncio
    async def test_list_running_by_skill(self, seeded_executions: list[SkillExecution]) -> None:
        """TEST-0806: List running executions by skill and stage.

        Covers AC-EC-002: Duplicate trigger prevention (detect running).
        """
        async with AsyncSessionLocal() as session:
            repo = SkillExecutionRepository(session)
            items = await repo.list_running_by_skill("skill-2", "stage-2")
            assert len(items) == 1
            assert items[0].overall_status == "RUNNING"

    @pytest.mark.asyncio
    async def test_list_running_by_skill_none(
        self, seeded_executions: list[SkillExecution]
    ) -> None:
        """TEST-0807: No running executions returns empty list.

        Covers edge case: no matching running executions.
        """
        async with AsyncSessionLocal() as session:
            repo = SkillExecutionRepository(session)
            items = await repo.list_running_by_skill("skill-1", "stage-1")
            assert len(items) == 0

    @pytest.mark.asyncio
    async def test_update(self, seeded_executions: list[SkillExecution]) -> None:
        """TEST-0808: Update execution status.

        Covers AC-F-006: Stage failure propagation.
        """
        async with AsyncSessionLocal() as session:
            repo = SkillExecutionRepository(session)
            exec_obj = await repo.get_by_id("exec-002")
            assert exec_obj is not None
            exec_obj.overall_status = "FAILED"
            updated = await repo.update(exec_obj)
            assert updated.overall_status == "FAILED"

    @pytest.mark.asyncio
    async def test_delete_success(self, seeded_executions: list[SkillExecution]) -> None:
        """TEST-0809: Delete existing execution returns True.

        Covers execution cleanup.
        """
        async with AsyncSessionLocal() as session:
            repo = SkillExecutionRepository(session)
            deleted = await repo.delete("exec-003")
            assert deleted is True
            assert await repo.get_by_id("exec-003") is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, seeded_executions: list[SkillExecution]) -> None:
        """TEST-0810: Delete nonexistent execution returns False.

        Covers edge case: idempotent deletion.
        """
        async with AsyncSessionLocal() as session:
            repo = SkillExecutionRepository(session)
            deleted = await repo.delete("no-such-exec")
            assert deleted is False
