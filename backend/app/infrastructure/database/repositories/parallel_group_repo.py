"""ParallelGroup repository with CRUD."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parallel_group import ParallelGroup


class ParallelGroupRepository:
    """Repository for ParallelGroup entity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, group: ParallelGroup) -> ParallelGroup:
        self._session.add(group)
        await self._session.commit()
        await self._session.refresh(group)
        return group

    async def create_batch(self, groups: list[ParallelGroup]) -> list[ParallelGroup]:
        self._session.add_all(groups)
        await self._session.commit()
        for group in groups:
            await self._session.refresh(group)
        return groups

    async def get_by_id(self, group_id: str) -> ParallelGroup | None:
        return await self._session.get(ParallelGroup, group_id)

    async def list_by_plan(self, plan_id: str) -> list[ParallelGroup]:
        stmt = select(ParallelGroup).where(ParallelGroup.plan_id == plan_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_plan(self, plan_id: str) -> None:
        stmt = select(ParallelGroup).where(ParallelGroup.plan_id == plan_id)
        result = await self._session.execute(stmt)
        for group in result.scalars().all():
            await self._session.delete(group)
        await self._session.commit()
