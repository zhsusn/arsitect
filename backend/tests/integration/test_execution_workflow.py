"""Integration test: end-to-end execution workflow."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project


class TestExecutionWorkflow:
    """End-to-end execution workflow integration test."""

    @pytest.fixture
    async def seeded_project(self) -> str:
        """Seed application and project, return project_id."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM execution_issues"))
            await session.execute(text("DELETE FROM execution_tasks"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-workflow",
                application_name="Workflow App",
                local_path="/tmp/workflow",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-workflow",
                project_name="Workflow Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj.project_id

    @pytest.mark.asyncio
    async def test_full_execution_workflow(
        self, seeded_project: str, client: TestClient
    ) -> None:
        """1. Create task → 2. Execute → 3. Fail → 4. Create issue → 5. Feedback → 6. Retry → verify."""
        project_id = seeded_project

        # 1. Create a task
        res = client.post(
            f"/api/v1/execution/{project_id}/tasks",
            json={"name": "Integration Task", "type": "coding"},
        )
        assert res.status_code == 201
        task = res.json()
        task_id = task["task_id"]
        assert task["status"] == "not_started"

        # 2. Execute the task
        res = client.post(f"/api/v1/execution/{project_id}/tasks/{task_id}/execute")
        assert res.status_code == 200
        task = res.json()
        assert task["status"] == "in_progress"

        # 3. Manually mark as failed to simulate execution failure
        res = client.patch(
            f"/api/v1/execution/{project_id}/tasks/{task_id}",
            json={"status": "failed"},
        )
        assert res.status_code == 200
        task = res.json()
        assert task["status"] == "failed"

        # 4. Create an issue for the failed task
        res = client.post(
            f"/api/v1/execution/{project_id}/issues",
            json={
                "task_id": task_id,
                "issue_type": "test_failure",
                "error_log": "integration test failed",
            },
        )
        assert res.status_code == 201
        issue = res.json()
        issue_id = issue["issue_id"]
        assert issue["status"] == "open"

        # 5. Mark issue as feedback to architecture
        res = client.patch(
            f"/api/v1/execution/{project_id}/issues/{issue_id}/feedback",
            json={"feedback_to_architecture": True},
        )
        assert res.status_code == 200
        issue = res.json()
        assert issue["feedback_to_architecture"] is True

        # 6. Retry the task
        res = client.post(f"/api/v1/execution/{project_id}/tasks/{task_id}/retry")
        assert res.status_code == 200
        task = res.json()
        assert task["status"] == "not_started"
        assert task["retry_count"] == 1

        # Verify: re-fetch task and issue to confirm persisted state
        res = client.get(f"/api/v1/execution/{project_id}/tasks")
        assert res.status_code == 200
        tasks = res.json()
        assert any(
            t["task_id"] == task_id and t["status"] == "not_started" for t in tasks
        )

        res = client.get(f"/api/v1/execution/{project_id}/issues")
        assert res.status_code == 200
        issues = res.json()
        assert any(
            i["issue_id"] == issue_id and i["feedback_to_architecture"] is True
            for i in issues
        )
