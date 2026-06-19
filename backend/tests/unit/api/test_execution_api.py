"""Tests for ExecutionRouter (tasks and issues)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.execution_issue import ExecutionIssue
from app.models.execution_task import ExecutionTask
from app.models.project import Project
from main import app

client = TestClient(app)


class TestExecutionRouter:
    """Execution router endpoint tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed application and project for execution tests."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM execution_issues"))
            await session.execute(text("DELETE FROM execution_tasks"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-exec",
                application_name="Exec App",
                local_path="/tmp/exec",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-exec",
                project_name="Exec Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.fixture
    async def seeded_task(self, seeded_project: Project) -> ExecutionTask:
        """Seed a single execution task."""
        async with AsyncSessionLocal() as session:
            task = ExecutionTask(
                task_id="task-exec-1",
                project_id=seeded_project.project_id,
                name="Seeded Task",
                type="coding",
                status="not_started",
            )
            session.add(task)
            await session.commit()
            return task

    @pytest.mark.asyncio
    async def test_get_tasks_empty(self, seeded_project: Project) -> None:
        """GET tasks returns empty list for project with no tasks."""
        res = client.get(f"/api/v1/execution/{seeded_project.project_id}/tasks")
        assert res.status_code == 200
        assert res.json() == []

    @pytest.mark.asyncio
    async def test_get_tasks_with_data(self, seeded_project: Project) -> None:
        """GET tasks returns created tasks."""
        async with AsyncSessionLocal() as session:
            task = ExecutionTask(
                task_id="task-exec-2",
                project_id=seeded_project.project_id,
                name="Task Two",
                type="test",
                status="not_started",
            )
            session.add(task)
            await session.commit()

        res = client.get(f"/api/v1/execution/{seeded_project.project_id}/tasks")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["task_id"] == "task-exec-2"

    @pytest.mark.asyncio
    async def test_create_task(self, seeded_project: Project) -> None:
        """POST creates a new task."""
        payload = {
            "name": "New Task",
            "type": "coding",
            "input_artifacts": ["req.md"],
            "assigned_skill_id": "skill-1",
            "parent_module": "mod-a",
            "output_artifact_path": "/out.py",
        }
        res = client.post(
            f"/api/v1/execution/{seeded_project.project_id}/tasks",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "New Task"
        assert data["type"] == "coding"
        assert data["status"] == "not_started"
        assert data["project_id"] == seeded_project.project_id

    @pytest.mark.asyncio
    async def test_create_task_invalid_type(self, seeded_project: Project) -> None:
        """POST with invalid type returns 422."""
        payload = {"name": "Bad Task", "type": "unknown"}
        res = client.post(
            f"/api/v1/execution/{seeded_project.project_id}/tasks",
            json=payload,
        )
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_update_task_status(self, seeded_task: ExecutionTask) -> None:
        """PATCH updates task status."""
        payload = {"status": "in_progress", "output_artifact_path": "/tmp/out.py"}
        res = client.patch(
            f"/api/v1/execution/{seeded_task.project_id}/tasks/{seeded_task.task_id}",
            json=payload,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "in_progress"
        assert data["output_artifact_path"] == "/tmp/out.py"

    @pytest.mark.asyncio
    async def test_execute_task(self, seeded_task: ExecutionTask) -> None:
        """POST execute moves task to in_progress."""
        res = client.post(
            f"/api/v1/execution/{seeded_task.project_id}/tasks/{seeded_task.task_id}/execute"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_execute_task_invalid_status(self, seeded_task: ExecutionTask) -> None:
        """POST execute on in_progress task returns 422."""
        async with AsyncSessionLocal() as session:
            task = await session.get(ExecutionTask, seeded_task.task_id)
            task.status = "in_progress"
            await session.commit()

        res = client.post(
            f"/api/v1/execution/{seeded_task.project_id}/tasks/{seeded_task.task_id}/execute"
        )
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_retry_task(self, seeded_task: ExecutionTask) -> None:
        """POST retry resets failed task to not_started."""
        async with AsyncSessionLocal() as session:
            task = await session.get(ExecutionTask, seeded_task.task_id)
            task.status = "failed"
            await session.commit()

        res = client.post(
            f"/api/v1/execution/{seeded_task.project_id}/tasks/{seeded_task.task_id}/retry"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "not_started"
        assert data["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_get_issues_empty(self, seeded_project: Project) -> None:
        """GET issues returns empty list for project with no issues."""
        res = client.get(f"/api/v1/execution/{seeded_project.project_id}/issues")
        assert res.status_code == 200
        assert res.json() == []

    @pytest.mark.asyncio
    async def test_get_issues_with_data(self, seeded_project: Project) -> None:
        """GET issues returns created issues."""
        async with AsyncSessionLocal() as session:
            issue = ExecutionIssue(
                issue_id="issue-exec-1",
                project_id=seeded_project.project_id,
                issue_type="compile_error",
                status="open",
            )
            session.add(issue)
            await session.commit()

        res = client.get(f"/api/v1/execution/{seeded_project.project_id}/issues")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["issue_id"] == "issue-exec-1"

    @pytest.mark.asyncio
    async def test_create_issue(self, seeded_project: Project) -> None:
        """POST creates a new issue."""
        payload = {
            "issue_type": "test_failure",
            "error_log": "assertion failed",
            "related_artifacts": ["test.py"],
            "suggested_action": "fix test",
        }
        res = client.post(
            f"/api/v1/execution/{seeded_project.project_id}/issues",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["issue_type"] == "test_failure"
        assert data["status"] == "open"
        assert data["project_id"] == seeded_project.project_id

    @pytest.mark.asyncio
    async def test_create_issue_invalid_type(self, seeded_project: Project) -> None:
        """POST with invalid issue type returns 422."""
        payload = {"issue_type": "bad_type"}
        res = client.post(
            f"/api/v1/execution/{seeded_project.project_id}/issues",
            json=payload,
        )
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_feedback_to_architecture(self, seeded_project: Project) -> None:
        """PATCH feedback toggles feedback_to_architecture."""
        async with AsyncSessionLocal() as session:
            issue = ExecutionIssue(
                issue_id="issue-exec-2",
                project_id=seeded_project.project_id,
                issue_type="arch_mismatch",
                status="open",
            )
            session.add(issue)
            await session.commit()

        res = client.patch(
            f"/api/v1/execution/{seeded_project.project_id}/issues/issue-exec-2/feedback",
            json={"feedback_to_architecture": True},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["feedback_to_architecture"] is True

        res = client.patch(
            f"/api/v1/execution/{seeded_project.project_id}/issues/issue-exec-2/feedback",
            json={"feedback_to_architecture": False},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["feedback_to_architecture"] is False
