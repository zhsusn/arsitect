"""SketchPageService — CRUD for generated sketch pages."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.sketch_page import SketchPage


class SketchPageService:
    """Handle sketch page lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self._session = session

    async def create_page(
        self,
        project_id: str,
        story_id: str | None,
        page_name: str,
        page_type: str,
        svg_content: str | None,
        fields_json: str | None,
        buttons_json: str | None,
        nav_targets_json: str | None,
        status: str,
        sort_order: int = 0,
        source_module_id: str | None = None,
        source_md_path: str | None = None,
    ) -> SketchPage:
        """Create a new sketch page."""
        page = SketchPage(
            page_id=f"spage-{uuid.uuid4()}",
            project_id=project_id,
            story_id=story_id,
            page_name=page_name,
            page_type=page_type,
            svg_content=svg_content,
            fields_json=fields_json,
            buttons_json=buttons_json,
            nav_targets_json=nav_targets_json,
            source_module_id=source_module_id,
            source_md_path=source_md_path,
            status=status,
            sort_order=sort_order,
        )
        self._session.add(page)
        await self._session.commit()
        await self._session.refresh(page)
        return page

    async def get_page(self, page_id: str) -> SketchPage:
        """Fetch a sketch page by ID."""
        result = await self._session.execute(
            select(SketchPage).where(SketchPage.page_id == page_id)
        )
        page = result.scalar_one_or_none()
        if page is None:
            raise NotFoundError(detail=f"SketchPage '{page_id}' not found")
        return page

    async def list_pages(self, project_id: str, story_id: str | None = None) -> list[SketchPage]:
        """List sketch pages for a project."""
        stmt = (
            select(SketchPage)
            .where(SketchPage.project_id == project_id)
            .order_by(SketchPage.sort_order.asc(), SketchPage.created_at.asc())
        )
        if story_id is not None:
            stmt = stmt.where(SketchPage.story_id == story_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_page(self, page_id: str, updates: dict[str, Any]) -> SketchPage:
        """Update an existing sketch page."""
        page = await self.get_page(page_id)
        for key, value in updates.items():
            if value is not None and hasattr(page, key):
                setattr(page, key, value)
        await self._session.commit()
        await self._session.refresh(page)
        return page

    async def delete_page(self, page_id: str) -> None:
        """Delete a sketch page."""
        page = await self.get_page(page_id)
        await self._session.delete(page)
        await self._session.commit()

    async def delete_by_project(self, project_id: str) -> None:
        """Delete all sketch pages for a project."""
        result = await self._session.execute(
            select(SketchPage).where(SketchPage.project_id == project_id)
        )
        for page in result.scalars().all():
            await self._session.delete(page)
        await self._session.commit()
