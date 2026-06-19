"""Task center business logic service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.repositories.execution_task_repo import ExecutionTaskRepository
from app.models.execution_issue import ExecutionIssue
from app.models.execution_task import ExecutionTask


class TaskCenterService:
    """Orchestrates execution task CRUD and lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session
        self._repo = ExecutionTaskRepository(session)

    async def get_tasks(self, project_id: str) -> list[ExecutionTask]:
        """Get all execution tasks for a project."""
        return await self._repo.get_by_project(project_id)

    async def get_task_by_id(self, task_id: str) -> ExecutionTask:
        """Get a single execution task by ID."""
        task = await self._repo.get_by_id(task_id)
        if task is None:
            raise NotFoundError(detail=f"Task '{task_id}' not found")
        return task

    async def create_task(
        self,
        project_id: str,
        name: str,
        type: str,
        input_artifacts: list[str] | None = None,
        assigned_skill_id: str | None = None,
        parent_module: str | None = None,
        output_artifact_path: str | None = None,
    ) -> ExecutionTask:
        """Create a new execution task."""
        valid_types = {"coding", "test", "bugfix"}
        if type not in valid_types:
            raise ValidationError(detail=f"Invalid task type '{type}'")

        task = ExecutionTask(
            task_id=str(uuid.uuid4()),
            project_id=project_id,
            name=name,
            type=type,
            status="not_started",
            input_artifacts=input_artifacts,
            assigned_skill_id=assigned_skill_id,
            parent_module=parent_module,
            output_artifact_path=output_artifact_path,
            retry_count=0,
        )
        return await self._repo.create(task)

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        output_artifact_path: str | None = None,
    ) -> ExecutionTask:
        """Update task status and optional output path."""
        valid_statuses = {"not_started", "in_progress", "passed", "failed", "blocked"}
        if status not in valid_statuses:
            raise ValidationError(detail=f"Invalid task status '{status}'")

        task = await self.get_task_by_id(task_id)
        task.status = status
        if output_artifact_path is not None:
            task.output_artifact_path = output_artifact_path
        task.updated_at = datetime.now(UTC)
        return await self._repo.update(task)

    async def execute_task(self, task_id: str) -> ExecutionTask:
        """Mark a task as running (execute)."""
        task = await self.get_task_by_id(task_id)
        if task.status not in {"not_started", "failed"}:
            raise ValidationError(
                detail=f"Cannot execute task in status '{task.status}'"
            )

        task.status = "in_progress"
        task.updated_at = datetime.now(UTC)
        return await self._repo.update(task)

    async def retry_task(self, task_id: str) -> ExecutionTask:
        """Retry a failed task."""
        task = await self.get_task_by_id(task_id)
        if task.status != "failed":
            raise ValidationError(detail="Only failed tasks can be retried")
        if task.retry_count >= 3:
            raise ValidationError(detail="Maximum retry count reached")

        task.status = "not_started"
        task.retry_count += 1
        task.updated_at = datetime.now(UTC)
        return await self._repo.update(task)

    async def mark_as_bug(
        self,
        task_id: str,
        error_log: str,
        issue_type: str,
    ) -> tuple[ExecutionTask, ExecutionIssue]:
        """Mark a failed task as blocked and create an associated issue."""
        task = await self.get_task_by_id(task_id)
        task.status = "blocked"
        task.updated_at = datetime.now(UTC)
        await self._repo.update(task)

        valid_types = {"compile_error", "test_failure", "arch_mismatch", "interface_mismatch", "other"}
        if issue_type not in valid_types:
            raise ValidationError(detail=f"Invalid issue type '{issue_type}'")

        issue = ExecutionIssue(
            issue_id=str(uuid.uuid4()),
            project_id=task.project_id,
            task_id=task_id,
            issue_type=issue_type,
            error_log=error_log,
            suggested_action="feedback",
            status="open",
        )
        self._session.add(issue)
        await self._session.commit()
        await self._session.refresh(issue)
        return task, issue

    async def auto_generate_tasks(
        self,
        project_id: str,
        design_artifact_ids: list[str] | None = None,
    ) -> list[ExecutionTask]:
        """Auto-generate execution tasks from design artifacts (mock implementation)."""
        tasks = []
        defaults = [
            {"name": "编码任务 — 核心模块", "type": "coding", "parent_module": "core"},
            {"name": "编码任务 — 接口层", "type": "coding", "parent_module": "api"},
            {"name": "单元测试 — 核心模块", "type": "test", "parent_module": "core"},
        ]
        for item in defaults:
            task = ExecutionTask(
                task_id=str(uuid.uuid4()),
                project_id=project_id,
                name=item["name"],
                type=item["type"],
                status="not_started",
                input_artifacts=design_artifact_ids or [],
                parent_module=item["parent_module"],
                retry_count=0,
            )
            self._session.add(task)
            tasks.append(task)
        await self._session.commit()
        for t in tasks:
            await self._session.refresh(t)
        return tasks
