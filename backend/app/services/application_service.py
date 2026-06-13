"""Application business logic service."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.application_repo import (
    ApplicationRepository,
)
from app.models.application import Application


class ApplicationService:
    """Orchestrates application CRUD and path validation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session
        self._repo = ApplicationRepository(session)

    async def create_application(
        self,
        *,
        application_id: str,
        application_name: str,
        local_path: str,
        description: str | None = None,
        workspace_id: str = "default",
    ) -> Application:
        """Create a new application with path validation."""
        path_accessible = Path(local_path).exists()
        app = Application(
            application_id=application_id,
            application_name=application_name,
            local_path=local_path,
            description=description,
            workspace_id=workspace_id,
            path_accessible=path_accessible,
        )
        return await self._repo.create(app)

    async def get_application(self, application_id: str) -> Application | None:
        """Fetch an application by ID."""
        return await self._repo.get_by_id(application_id)

    async def list_applications(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        workspace_id: str | None = None,
    ) -> tuple[list[Application], int]:
        """List all applications."""
        return await self._repo.list_all(
            page=page, page_size=page_size, workspace_id=workspace_id
        )

    async def update_application(
        self,
        application_id: str,
        *,
        application_name: str | None = None,
        local_path: str | None = None,
        description: str | None = None,
    ) -> Application | None:
        """Update an application."""
        app = await self._repo.get_by_id(application_id)
        if app is None:
            return None
        if application_name is not None:
            app.application_name = application_name
        if local_path is not None:
            app.local_path = local_path
            app.path_accessible = Path(local_path).exists()
        if description is not None:
            app.description = description
        return await self._repo.update(app)

    async def delete_application(self, application_id: str) -> bool:
        """Delete an application."""
        return await self._repo.delete(application_id)

    async def check_path_accessibility(self, application_id: str) -> bool:
        """Re-check and update path accessibility."""
        app = await self._repo.get_by_id(application_id)
        if app is None:
            return False
        accessible = Path(app.local_path).exists()
        app.path_accessible = accessible
        await self._repo.update(app)
        return accessible
