"""WireframePageService — CRUD for generated wireframe pages."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.wireframe_page import WireframePage


class WireframePageService:
    """Handle wireframe page lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._session = session

    async def create_page(
        self,
        wireframe_id: str,
        project_id: str,
        entity_id: str | None,
        entity_name: str | None,
        page_name: str,
        page_type: str,
        confidence: int | None,
        mapping_source: str,
        svg_content: str | None,
        layout_json: str | None,
        status: str,
        sort_order: int = 0,
    ) -> WireframePage:
        """Create a new wireframe page."""
        page = WireframePage(
            page_id=f"wfpage-{uuid.uuid4()}",
            wireframe_id=wireframe_id,
            project_id=project_id,
            entity_id=entity_id,
            entity_name=entity_name,
            page_name=page_name,
            page_type=page_type,
            confidence=confidence,
            mapping_source=mapping_source,
            svg_content=svg_content,
            layout_json=layout_json,
            status=status,
            sort_order=sort_order,
        )
        self._session.add(page)
        await self._session.flush()
        return page

    async def get_page(self, page_id: str) -> WireframePage:
        """Fetch a wireframe page by ID."""
        result = await self._session.execute(
            select(WireframePage).where(WireframePage.page_id == page_id)
        )
        page = result.scalar_one_or_none()
        if page is None:
            raise NotFoundError(detail=f"WireframePage '{page_id}' not found")
        return page

    async def list_pages(
        self, project_id: str, wireframe_id: str | None = None
    ) -> list[WireframePage]:
        """List wireframe pages for a project."""
        stmt = (
            select(WireframePage)
            .where(WireframePage.project_id == project_id)
            .order_by(WireframePage.sort_order.asc(), WireframePage.created_at.asc())
        )
        if wireframe_id is not None:
            stmt = stmt.where(WireframePage.wireframe_id == wireframe_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_page(self, page_id: str, updates: dict[str, Any]) -> WireframePage:
        """Update an existing wireframe page."""
        page = await self.get_page(page_id)
        for key, value in updates.items():
            if value is not None and hasattr(page, key):
                setattr(page, key, value)
        await self._session.flush()
        return page

    async def delete_page(self, page_id: str) -> None:
        """Delete a wireframe page."""
        page = await self.get_page(page_id)
        await self._session.delete(page)
        await self._session.flush()

    async def delete_by_wireframe(self, wireframe_id: str) -> None:
        """Delete all wireframe pages for a wireframe session."""
        result = await self._session.execute(
            select(WireframePage).where(WireframePage.wireframe_id == wireframe_id)
        )
        for page in result.scalars().all():
            await self._session.delete(page)
        await self._session.flush()
