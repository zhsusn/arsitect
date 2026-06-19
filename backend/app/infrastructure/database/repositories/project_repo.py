"""Project repository with CRUD and state transitions."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    """Repository for Project entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def create(self, project: Project) -> Project:
        """Create a new project record."""
        self._session.add(project)
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def get_by_id(self, project_id: str) -> Project | None:
        """Fetch a project by its primary key."""
        return await self._session.get(Project, project_id)

    async def list_by_application(
        self,
        application_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Project], int]:
        """List projects by application ID with total count."""
        offset = (page - 1) * page_size
        stmt = (
            select(Project)
            .where(Project.application_id == application_id)
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        count_stmt = (
            select(func.count())
            .select_from(Project)
            .where(Project.application_id == application_id)
        )
        total = await self._session.scalar(count_stmt) or 0
        return items, total

    async def update(self, project: Project) -> Project:
        """Update an existing project."""
        self._session.add(project)
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def delete(self, project_id: str) -> bool:
        """Delete a project by ID. Returns True if deleted."""
        proj = await self.get_by_id(project_id)
        if proj is None:
            return False
        await self._session.delete(proj)
        await self._session.commit()
        return True

    async def exists_by_name(self, application_id: str, project_name: str) -> bool:
        """Check if a project with the given name exists in the application."""
        stmt = (
            select(func.count())
            .select_from(Project)
            .where(
                Project.application_id == application_id,
                Project.project_name == project_name,
                Project.project_status.in_(["Draft", "Active", "Cancelled"]),
            )
        )
        count = await self._session.scalar(stmt) or 0
        return count > 0
