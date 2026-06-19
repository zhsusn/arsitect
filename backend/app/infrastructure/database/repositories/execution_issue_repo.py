"""ExecutionIssue repository with CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_issue import ExecutionIssue


class ExecutionIssueRepository:
    """Repository for ExecutionIssue entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def get_by_project(self, project_id: str) -> list[ExecutionIssue]:
        """Fetch all execution issues for a project, newest first."""
        stmt = (
            select(ExecutionIssue)
            .where(ExecutionIssue.project_id == project_id)
            .order_by(ExecutionIssue.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, issue_id: str) -> ExecutionIssue | None:
        """Fetch an execution issue by its primary key."""
        return await self._session.get(ExecutionIssue, issue_id)

    async def create(self, issue: ExecutionIssue) -> ExecutionIssue:
        """Persist a new execution issue."""
        self._session.add(issue)
        await self._session.commit()
        await self._session.refresh(issue)
        return issue

    async def update(self, issue: ExecutionIssue) -> ExecutionIssue:
        """Update an existing execution issue."""
        self._session.add(issue)
        await self._session.commit()
        await self._session.refresh(issue)
        return issue
