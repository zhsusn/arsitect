"""WireframeNavLinkService — CRUD for page navigation links."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.wireframe_nav_link import WireframeNavLink


class WireframeNavLinkService:
    """Handle wireframe navigation link lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._session = session

    async def create_link(
        self,
        wireframe_id: str,
        project_id: str,
        source_page_id: str,
        target_page_id: str,
        interface_refs_json: str | None,
        relation_strength: str,
        interface_count: int,
    ) -> WireframeNavLink:
        """Create a new nav link."""
        link = WireframeNavLink(
            link_id=f"navlink-{uuid.uuid4()}",
            wireframe_id=wireframe_id,
            project_id=project_id,
            source_page_id=source_page_id,
            target_page_id=target_page_id,
            interface_refs_json=interface_refs_json,
            relation_strength=relation_strength,
            interface_count=interface_count,
        )
        self._session.add(link)
        await self._session.flush()
        return link

    async def get_link(self, link_id: str) -> WireframeNavLink:
        """Fetch a nav link by ID."""
        result = await self._session.execute(
            select(WireframeNavLink).where(WireframeNavLink.link_id == link_id)
        )
        link = result.scalar_one_or_none()
        if link is None:
            raise NotFoundError(detail=f"WireframeNavLink '{link_id}' not found")
        return link

    async def list_links(
        self, project_id: str, wireframe_id: str | None = None
    ) -> list[WireframeNavLink]:
        """List nav links for a project."""
        stmt = select(WireframeNavLink).where(WireframeNavLink.project_id == project_id)
        if wireframe_id is not None:
            stmt = stmt.where(WireframeNavLink.wireframe_id == wireframe_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_link(self, link_id: str, updates: dict[str, Any]) -> WireframeNavLink:
        """Update an existing nav link."""
        link = await self.get_link(link_id)
        for key, value in updates.items():
            if value is not None and hasattr(link, key):
                setattr(link, key, value)
        await self._session.flush()
        return link

    async def delete_link(self, link_id: str) -> None:
        """Delete a nav link."""
        link = await self.get_link(link_id)
        await self._session.delete(link)
        await self._session.flush()

    async def delete_by_wireframe(self, wireframe_id: str) -> None:
        """Delete all nav links for a wireframe session."""
        result = await self._session.execute(
            select(WireframeNavLink).where(WireframeNavLink.wireframe_id == wireframe_id)
        )
        for link in result.scalars().all():
            await self._session.delete(link)
        await self._session.flush()
