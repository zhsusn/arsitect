"""SkillExecution repository with CRUD."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_execution import SkillExecution


class SkillExecutionRepository:
    """Repository for SkillExecution entity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, execution: SkillExecution) -> SkillExecution:
        self._session.add(execution)
        await self._session.commit()
        await self._session.refresh(execution)
        return execution

    async def get_by_id(self, execution_id: str) -> SkillExecution | None:
        return await self._session.get(SkillExecution, execution_id)

    async def list_by_project(self, project_id: str) -> list[SkillExecution]:
        stmt = (
            select(SkillExecution)
            .where(SkillExecution.project_id == project_id)
            .order_by(SkillExecution.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_stage(self, stage_id: str) -> list[SkillExecution]:
        stmt = (
            select(SkillExecution)
            .where(SkillExecution.stage_id == stage_id)
            .order_by(SkillExecution.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_running_by_skill(self, skill_id: str, stage_id: str) -> list[SkillExecution]:
        stmt = select(SkillExecution).where(
            SkillExecution.skill_id == skill_id,
            SkillExecution.stage_id == stage_id,
            SkillExecution.overall_status == "RUNNING",
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, execution: SkillExecution) -> SkillExecution:
        self._session.add(execution)
        await self._session.commit()
        await self._session.refresh(execution)
        return execution

    async def delete(self, execution_id: str) -> bool:
        execution = await self.get_by_id(execution_id)
        if execution is None:
            return False
        await self._session.delete(execution)
        await self._session.commit()
        return True
