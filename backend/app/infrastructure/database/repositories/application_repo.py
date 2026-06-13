"""Application repository with CRUD operations."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application


class ApplicationRepository:
    """Repository for Application entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def create(self, application: Application) -> Application:
        """Create a new application record."""
        self._session.add(application)
        await self._session.commit()
        await self._session.refresh(application)
        return application

    async def get_by_id(self, application_id: str) -> Application | None:
        """Fetch an application by its primary key."""
        return await self._session.get(Application, application_id)

    async def list_all(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        workspace_id: str | None = None,
    ) -> tuple[list[Application], int]:
        """List applications with total count."""
        offset = (page - 1) * page_size
        stmt = select(Application)
        count_stmt = select(func.count()).select_from(Application)

        if workspace_id is not None:
            stmt = stmt.where(Application.workspace_id == workspace_id)
            count_stmt = count_stmt.where(
                Application.workspace_id == workspace_id
            )

        stmt = stmt.offset(offset).limit(page_size)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        total = await self._session.scalar(count_stmt) or 0
        return items, total

    async def update(self, application: Application) -> Application:
        """Update an existing application."""
        self._session.add(application)
        await self._session.commit()
        await self._session.refresh(application)
        return application

    async def delete(self, application_id: str) -> bool:
        """Delete an application by ID. Returns True if deleted."""
        app = await self.get_by_id(application_id)
        if app is None:
            return False
        await self._session.delete(app)
        await self._session.commit()
        return True
