"""CanvasState repository with CRUD operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canvas_state import CanvasState


class CanvasStateRepository:
    """Repository for CanvasState entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def get_by_project_id(self, project_id: str) -> CanvasState | None:
        """Fetch canvas state by project ID."""
        stmt = select(CanvasState).where(CanvasState.project_id == project_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, canvas_state: CanvasState) -> CanvasState:
        """Create or update a canvas state record."""
        self._session.add(canvas_state)
        await self._session.commit()
        await self._session.refresh(canvas_state)
        return canvas_state

    async def delete_by_project_id(self, project_id: str) -> bool:
        """Delete canvas state by project ID. Returns True if deleted."""
        entity = await self.get_by_project_id(project_id)
        if entity is None:
            return False
        await self._session.delete(entity)
        await self._session.commit()
        return True
