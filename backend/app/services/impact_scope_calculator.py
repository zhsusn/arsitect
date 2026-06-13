"""Impact scope calculator — evaluates template switch effects."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_stage import ProjectStage
from app.models.template_stage import TemplateStage


class ImpactScopeCalculator:
    """Calculates the impact of switching a project to a different template."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def calculate_impact(
        self,
        project_id: str,
        new_template_id: str,
    ) -> dict[str, Any]:
        """Compare current project stages against a new template.

        Returns counts of frozen, removed, and added stages.
        """
        current_stages = await self._get_project_stages(project_id)
        new_stages = await self._get_template_stages(new_template_id)

        current_stage_ids = {s.stage_id for s in current_stages}
        new_stage_ids = {s.stage_id for s in new_stages}

        frozen = []
        removed = []
        retained = []

        for stage in current_stages:
            if stage.status in ("EXECUTED", "FROZEN", "ARCHIVED"):
                frozen.append(stage)
            elif stage.stage_id not in new_stage_ids:
                removed.append(stage)
            else:
                retained.append(stage)

        added = [s for s in new_stages if s.stage_id not in current_stage_ids]

        return {
            "frozen_count": len(frozen),
            "removed_count": len(removed),
            "added_count": len(added),
            "retained_count": len(retained),
            "frozen_stages": frozen,
            "removed_stages": removed,
            "added_stages": added,
            "retained_stages": retained,
        }

    async def _get_project_stages(self, project_id: str) -> list[ProjectStage]:
        stmt = (
            select(ProjectStage)
            .where(ProjectStage.project_id == project_id)
            .order_by(ProjectStage.order_index)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def _get_template_stages(
        self, template_id: str
    ) -> list[TemplateStage]:
        stmt = (
            select(TemplateStage)
            .where(TemplateStage.template_id == template_id)
            .order_by(TemplateStage.order_index)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
