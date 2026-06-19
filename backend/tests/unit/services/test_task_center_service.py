"""Unit tests for TaskCenterService."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.execution_task import ExecutionTask
from app.models.project import Project
from app.services.task_center_service import TaskCenterService


class TestTaskCenterService:
    """TaskCenterService CRUD and lifecycle tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project for task tests."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM execution_tasks"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-task",
                application_name="Task App",
                local_path="/tmp/task",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-task",
                project_name="Task Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    async def test_get_tasks_empty(self) -> None:
        """get_tasks returns empty list when no tasks exist."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            tasks = await svc.get_tasks("proj-empty")
            assert tasks == []

    async def test_get_tasks_with_data(self, seeded_project: Project) -> None:
        """get_tasks returns tasks ordered by created_at desc."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            task1 = await svc.create_task(seeded_project.project_id, "Task A", "coding")
            task2 = await svc.create_task(seeded_project.project_id, "Task B", "test")
            tasks = await svc.get_tasks(seeded_project.project_id)
            assert len(tasks) == 2
            assert tasks[0].task_id == task2.task_id
            assert tasks[1].task_id == task1.task_id

    async def test_create_task_valid(self, seeded_project: Project) -> None:
        """create_task with valid type sets default status."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            task = await svc.create_task(
                seeded_project.project_id,
                "New Task",
                "bugfix",
                input_artifacts=["a.md"],
                assigned_skill_id="skill-1",
            )
            assert task.name == "New Task"
            assert task.type == "bugfix"
            assert task.status == "not_started"
            assert task.retry_count == 0
            assert task.input_artifacts == ["a.md"]

    async def test_create_task_invalid_type(self, seeded_project: Project) -> None:
        """create_task raises ValidationError for invalid type."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            with pytest.raises(ValidationError):
                await svc.create_task(seeded_project.project_id, "Bad Task", "invalid_type")

    async def test_update_task_status_valid(self, seeded_project: Project) -> None:
        """update_task_status changes status and output path."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            task = await svc.create_task(seeded_project.project_id, "Task", "coding")
            updated = await svc.update_task_status(
                task.task_id, "passed", output_artifact_path="/out.py"
            )
            assert updated.status == "passed"
            assert updated.output_artifact_path == "/out.py"

    async def test_update_task_status_invalid(self, seeded_project: Project) -> None:
        """update_task_status raises ValidationError for bad status."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            task = await svc.create_task(seeded_project.project_id, "Task", "coding")
            with pytest.raises(ValidationError):
                await svc.update_task_status(task.task_id, "unknown_status")

    async def test_update_task_status_not_found(self) -> None:
        """update_task_status raises NotFoundError for missing task."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            with pytest.raises(NotFoundError):
                await svc.update_task_status("no-such-id", "passed")

    async def test_execute_task_pending(self, seeded_project: Project) -> None:
        """execute_task moves pending task to in_progress."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            task = await svc.create_task(seeded_project.project_id, "Task", "coding")
            executed = await svc.execute_task(task.task_id)
            assert executed.status == "in_progress"

    async def test_execute_task_failed(self, seeded_project: Project) -> None:
        """execute_task allows retry from failed."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            task = await svc.create_task(seeded_project.project_id, "Task", "coding")
            await svc.update_task_status(task.task_id, "failed")
            executed = await svc.execute_task(task.task_id)
            assert executed.status == "in_progress"

    async def test_execute_task_invalid_status(self, seeded_project: Project) -> None:
        """execute_task raises ValidationError for in_progress task."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            task = await svc.create_task(seeded_project.project_id, "Task", "coding")
            await svc.update_task_status(task.task_id, "in_progress")
            with pytest.raises(ValidationError):
                await svc.execute_task(task.task_id)

    async def test_execute_task_not_found(self) -> None:
        """execute_task raises NotFoundError for missing task."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            with pytest.raises(NotFoundError):
                await svc.execute_task("no-such-id")

    async def test_retry_task_failed(self, seeded_project: Project) -> None:
        """retry_task resets failed task to not_started and increments retry."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            task = await svc.create_task(seeded_project.project_id, "Task", "coding")
            await svc.update_task_status(task.task_id, "failed")
            retried = await svc.retry_task(task.task_id)
            assert retried.status == "not_started"
            assert retried.retry_count == 1

    async def test_retry_task_max_retries(self, seeded_project: Project) -> None:
        """retry_task raises ValidationError when max retries reached."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            task = await svc.create_task(seeded_project.project_id, "Task", "coding")
            for _ in range(3):
                await svc.update_task_status(task.task_id, "failed")
                await svc.retry_task(task.task_id)
            await svc.update_task_status(task.task_id, "failed")
            with pytest.raises(ValidationError, match="Maximum retry count reached"):
                await svc.retry_task(task.task_id)

    async def test_retry_task_non_failed(self, seeded_project: Project) -> None:
        """retry_task raises ValidationError for non-failed task."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            task = await svc.create_task(seeded_project.project_id, "Task", "coding")
            with pytest.raises(ValidationError):
                await svc.retry_task(task.task_id)

    async def test_retry_task_not_found(self) -> None:
        """retry_task raises NotFoundError for missing task."""
        async with AsyncSessionLocal() as session:
            svc = TaskCenterService(session)
            with pytest.raises(NotFoundError):
                await svc.retry_task("no-such-id")
