"""Unit tests for ExecutionIssueService."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.execution_issue import ExecutionIssue
from app.models.execution_task import ExecutionTask
from app.models.project import Project
from app.services.execution_issue_service import ExecutionIssueService
from app.services.task_center_service import TaskCenterService


class TestExecutionIssueService:
    """ExecutionIssueService CRUD and feedback tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project for issue tests."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM execution_issues"))
            await session.execute(text("DELETE FROM execution_tasks"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-issue",
                application_name="Issue App",
                local_path="/tmp/issue",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-issue",
                project_name="Issue Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.fixture
    async def seeded_task(self, seeded_project: Project) -> ExecutionTask:
        """Seed a single execution task for the project."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            task = await svc.create_task(
                seeded_project.project_id, "Issue Task", "coding"
            )
            return task

    async def test_get_issues_empty(self) -> None:
        """get_issues returns empty list when no issues exist."""
        async with AsyncSessionLocal() as session:
            svc = ExecutionIssueService(session)
            issues = await svc.get_issues("proj-empty")
            assert issues == []

    async def test_get_issues_with_data(self, seeded_project: Project) -> None:
        """get_issues returns issues ordered by created_at desc."""
        async with AsyncSessionLocal() as session:
            svc = ExecutionIssueService(session)
            issue1 = await svc.create_issue(
                seeded_project.project_id, None, "compile_error"
            )
            issue2 = await svc.create_issue(
                seeded_project.project_id, None, "test_failure"
            )
            issues = await svc.get_issues(seeded_project.project_id)
            assert len(issues) == 2
            assert issues[0].issue_id == issue2.issue_id
            assert issues[1].issue_id == issue1.issue_id

    async def test_create_issue_valid(self, seeded_project: Project, seeded_task: ExecutionTask) -> None:
        """create_issue with valid type sets default status."""
        async with AsyncSessionLocal() as session:
            svc = ExecutionIssueService(session)
            issue = await svc.create_issue(
                seeded_project.project_id,
                task_id=seeded_task.task_id,
                issue_type="arch_mismatch",
                error_log="error",
                related_artifacts=["a.md"],
                suggested_action="fix",
            )
            assert issue.issue_type == "arch_mismatch"
            assert issue.status == "open"
            assert issue.task_id == seeded_task.task_id
            assert issue.error_log == "error"

    async def test_create_issue_invalid_type(self, seeded_project: Project) -> None:
        """create_issue raises ValidationError for invalid type."""
        async with AsyncSessionLocal() as session:
            svc = ExecutionIssueService(session)
            with pytest.raises(ValidationError):
                await svc.create_issue(seeded_project.project_id, None, "bad_type")

    async def test_feedback_to_architecture_toggle(self, seeded_project: Project) -> None:
        """feedback_to_architecture toggles bool and returns updated issue."""
        async with AsyncSessionLocal() as session:
            svc = ExecutionIssueService(session)
            issue = await svc.create_issue(
                seeded_project.project_id, None, "other"
            )
            assert issue.feedback_to_architecture is False

            updated = await svc.feedback_to_architecture(issue.issue_id, True)
            assert updated.feedback_to_architecture is True

            updated = await svc.feedback_to_architecture(issue.issue_id, False)
            assert updated.feedback_to_architecture is False

    async def test_feedback_to_architecture_not_found(self) -> None:
        """feedback_to_architecture raises NotFoundError for missing issue."""
        async with AsyncSessionLocal() as session:
            svc = ExecutionIssueService(session)
            with pytest.raises(NotFoundError):
                await svc.feedback_to_architecture("no-such-id", True)
