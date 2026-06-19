"""Skill registry service — queries and DAG state management."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.models.skill_changelog import SkillChangeLog
from app.models.skill_dag import SkillDAGEdge, SkillDAGNode
from app.models.skill_execution import SkillExecution
from app.models.template_stage import TemplateStage


class SkillRegistryService:
    """Lightweight service for skill queries and DAG state."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def list_skills(
        self,
        *,
        search: str | None = None,
        pattern: str | None = None,
        status: str | None = None,
    ) -> list[Skill]:
        """List skills with optional filters."""
        stmt = select(Skill)
        if search:
            stmt = stmt.where(Skill.skill_name.ilike(f"%{search}%"))
        if pattern:
            stmt = stmt.where(Skill.pattern == pattern)
        if status:
            stmt = stmt.where(Skill.parse_status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_skill(self, skill_id: str) -> Skill | None:
        """Fetch a skill by ID."""
        return await self._session.get(Skill, skill_id)

    async def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill by ID. Returns True if deleted."""
        skill = await self.get_skill(skill_id)
        if skill is None:
            return False
        await self._session.delete(skill)
        await self._session.commit()
        return True

    async def get_dag(self) -> dict[str, list[Any]]:
        """Fetch all DAG nodes and edges."""
        nodes_result = await self._session.execute(select(SkillDAGNode))
        edges_result = await self._session.execute(select(SkillDAGEdge))
        return {
            "nodes": list(nodes_result.scalars().all()),
            "edges": list(edges_result.scalars().all()),
        }

    async def get_changelog(
        self,
        session_id: str | None = None,
    ) -> list[SkillChangeLog]:
        """Fetch DAG change logs, optionally filtered by session."""
        stmt = select(SkillChangeLog)
        if session_id:
            stmt = stmt.where(SkillChangeLog.session_id == session_id)
        stmt = stmt.order_by(SkillChangeLog.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_skill_executions(
        self,
        skill_id: str,
        limit: int = 5,
    ) -> list[SkillExecution]:
        """Fetch recent execution history for a skill."""
        stmt = (
            select(SkillExecution)
            .where(SkillExecution.skill_id == skill_id)
            .order_by(SkillExecution.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_bound_stages(
        self,
        skill_id: str,
    ) -> list[dict[str, Any]]:
        """Fetch stages that bind this skill as primary or auxiliary."""
        stages: list[dict[str, Any]] = []

        # Primary binding
        primary_stmt = select(TemplateStage).where(TemplateStage.primary_skill_id == skill_id)
        primary_result = await self._session.execute(primary_stmt)
        for stage in primary_result.scalars().all():
            stages.append(
                {
                    "stage_id": stage.stage_id,
                    "stage_name": stage.stage_name,
                    "template_id": stage.template_id,
                    "binding_type": "primary",
                }
            )

        # Auxiliary binding — brute-force scan since auxiliary_skill_ids is JSON text
        aux_stmt = select(TemplateStage)
        aux_result = await self._session.execute(aux_stmt)
        for stage in aux_result.scalars().all():
            if stage.auxiliary_skill_ids:
                try:
                    aux_ids: list[str] = json.loads(stage.auxiliary_skill_ids)
                    if skill_id in aux_ids:
                        stages.append(
                            {
                                "stage_id": stage.stage_id,
                                "stage_name": stage.stage_name,
                                "template_id": stage.template_id,
                                "binding_type": "auxiliary",
                            }
                        )
                except json.JSONDecodeError:
                    continue

        return stages
