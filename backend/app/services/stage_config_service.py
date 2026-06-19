"""Stage config service — assembles template-stage sequences."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.governance.template_engine import Deviation, TemplateEngine
from app.infrastructure.database.repositories.template_repo import TemplateRepository
from app.models.template import Template
from app.models.template_stage import TemplateStage


class StageConfigService:
    """Provides template and stage configuration queries."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session
        self._repo = TemplateRepository(session)
        self._engine = TemplateEngine()

    async def list_templates(self) -> list[Template]:
        """List all predefined templates."""
        return await self._repo.list_templates()

    async def update_execution_strategy(
        self, template_id: str, execution_strategy: str
    ) -> Template:
        """Update a template's default execution strategy."""
        valid_strategies = {"full_auto", "semi_auto", "full_manual"}
        if execution_strategy not in valid_strategies:
            raise ValidationError(
                detail=f"Invalid execution_strategy '{execution_strategy}'"
            )
        tpl = await self._repo.get_template(template_id)
        if tpl is None:
            raise NotFoundError(detail=f"Template '{template_id}' not found")
        tpl.default_execution_strategy = execution_strategy
        await self._session.commit()
        await self._session.refresh(tpl)
        return tpl

    async def get_template_detail(self, template_id: str) -> dict[str, Any]:
        """Get a template with its ordered stage sequence."""
        tpl = await self._repo.get_template(template_id)
        if tpl is None:
            raise NotFoundError(detail=f"Template '{template_id}' not found")
        stages = await self._repo.get_stages_for_template(template_id)
        return {"template": tpl, "stages": stages}

    async def get_stage_sequence(self, template_id: str) -> list[TemplateStage]:
        """Get the ordered stage list for a template."""
        tpl = await self._repo.get_template(template_id)
        if tpl is None:
            raise NotFoundError(detail=f"Template '{template_id}' not found")
        return await self._repo.get_stages_for_template(template_id)

    def get_default_template(self, route: str) -> dict[str, Any] | None:
        """Return the in-memory default template for a route."""
        template = self._engine.get_template(route)
        if template is None:
            return None
        return {
            "route": template.route,
            "description": template.description,
            "execution_strategy": template.execution_strategy,
            "merge_policy": template.get_merge_policy(),
            "stages": [
                {
                    "business_stage_key": s.business_stage_key,
                    "stage_name": s.stage_name,
                    "primary_skill_id": s.primary_skill_id,
                    "auxiliary_skill_ids": s.auxiliary_skill_ids,
                    "order": s.order,
                    "is_gate_required": s.is_gate_required,
                    "auto_advance": s.auto_advance,
                }
                for s in template.stages
            ],
        }

    def compute_deviations(
        self,
        project_id: str,
        template_route: str,
        actual_stages: list[str],
    ) -> list[Deviation]:
        """Compute stage deviations against the default template."""
        deviations: list[Deviation] = []
        self._engine.record_deviation(deviations, project_id, template_route, actual_stages)
        return deviations

    async def update_stage(
        self,
        stage_id: str,
        *,
        primary_skill_id: str | None = None,
        auxiliary_skill_ids: list[str] | None = None,
    ) -> TemplateStage:
        """Update skill bindings for a template stage."""
        from sqlalchemy import select

        stmt = select(TemplateStage).where(TemplateStage.stage_id == stage_id)
        result = await self._session.execute(stmt)
        stage = result.scalar_one_or_none()
        if stage is None:
            raise NotFoundError(detail=f"Stage '{stage_id}' not found")

        if primary_skill_id is not None:
            stage.primary_skill_id = primary_skill_id
        if auxiliary_skill_ids is not None:
            import json

            stage.auxiliary_skill_ids = json.dumps(auxiliary_skill_ids)

        await self._session.commit()
        await self._session.refresh(stage)
        return stage
