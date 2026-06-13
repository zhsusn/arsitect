"""OpenUIPageService — CRUD for OpenUI generated pages."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.open_ui_page import OpenUIPage


class OpenUIPageService:
    """Handle OpenUI page lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._session = session

    async def create_page(
        self,
        spec_id: str,
        project_id: str,
        container_id: str | None,
        page_title: str,
        html_content: str | None,
        page_index: int,
        status: str,
    ) -> OpenUIPage:
        """Create a new OpenUI page."""
        page = OpenUIPage(
            page_id=f"opage-{uuid.uuid4()}",
            spec_id=spec_id,
            project_id=project_id,
            container_id=container_id,
            page_title=page_title,
            html_content=html_content,
            page_index=page_index,
            status=status,
        )
        self._session.add(page)
        await self._session.flush()
        return page

    async def get_page(self, page_id: str) -> OpenUIPage:
        """Fetch a page by ID."""
        result = await self._session.execute(
            select(OpenUIPage).where(OpenUIPage.page_id == page_id)
        )
        page = result.scalar_one_or_none()
        if page is None:
            raise NotFoundError(detail=f"OpenUIPage '{page_id}' not found")
        return page

    async def list_pages(
        self, project_id: str, spec_id: str | None = None
    ) -> list[OpenUIPage]:
        """List OpenUI pages for a project."""
        stmt = (
            select(OpenUIPage)
            .where(OpenUIPage.project_id == project_id)
            .order_by(OpenUIPage.page_index.asc(), OpenUIPage.created_at.asc())
        )
        if spec_id is not None:
            stmt = stmt.where(OpenUIPage.spec_id == spec_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_page(
        self, page_id: str, updates: dict[str, Any]
    ) -> OpenUIPage:
        """Update an existing page."""
        page = await self.get_page(page_id)
        for key, value in updates.items():
            if value is not None and hasattr(page, key):
                setattr(page, key, value)
        await self._session.flush()
        return page

    async def delete_page(self, page_id: str) -> None:
        """Delete a page."""
        page = await self.get_page(page_id)
        await self._session.delete(page)
        await self._session.flush()

    async def delete_by_spec(self, spec_id: str) -> None:
        """Delete all pages for a spec."""
        result = await self._session.execute(
            select(OpenUIPage).where(OpenUIPage.spec_id == spec_id)
        )
        for page in result.scalars().all():
            await self._session.delete(page)
        await self._session.flush()
