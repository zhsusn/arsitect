"""Template repository — queries for templates and their stages."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template
from app.models.template_stage import TemplateStage


class TemplateRepository:
    """Repository for Template and TemplateStage entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def list_templates(self) -> list[Template]:
        """List all predefined templates."""
        stmt = select(Template)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_template(self, template_id: str) -> Template | None:
        """Fetch a template by its primary key."""
        return await self._session.get(Template, template_id)

    async def get_stages_for_template(self, template_id: str) -> list[TemplateStage]:
        """Fetch ordered stages for a given template."""
        stmt = (
            select(TemplateStage)
            .where(TemplateStage.template_id == template_id)
            .order_by(TemplateStage.order_index)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
