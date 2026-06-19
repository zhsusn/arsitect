"""ExecutionTask repository with CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_task import ExecutionTask


class ExecutionTaskRepository:
    """Repository for ExecutionTask entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def get_by_project(self, project_id: str) -> list[ExecutionTask]:
        """Fetch all execution tasks for a project, newest first."""
        stmt = (
            select(ExecutionTask)
            .where(ExecutionTask.project_id == project_id)
            .order_by(ExecutionTask.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, task_id: str) -> ExecutionTask | None:
        """Fetch an execution task by its primary key."""
        return await self._session.get(ExecutionTask, task_id)

    async def create(self, task: ExecutionTask) -> ExecutionTask:
        """Persist a new execution task."""
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def update(self, task: ExecutionTask) -> ExecutionTask:
        """Update an existing execution task."""
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def delete(self, task_id: str) -> bool:
        """Delete an execution task by ID. Returns True if deleted."""
        task = await self.get_by_id(task_id)
        if task is None:
            return False
        await self._session.delete(task)
        await self._session.commit()
        return True
