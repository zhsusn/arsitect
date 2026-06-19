"""PlanNode repository with CRUD and status queries."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan_node import PlanNode


class PlanNodeRepository:
    """Repository for PlanNode entity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, node: PlanNode) -> PlanNode:
        self._session.add(node)
        await self._session.commit()
        await self._session.refresh(node)
        return node

    async def create_batch(self, nodes: list[PlanNode]) -> list[PlanNode]:
        self._session.add_all(nodes)
        await self._session.commit()
        for node in nodes:
            await self._session.refresh(node)
        return nodes

    async def get_by_id(self, node_id: str) -> PlanNode | None:
        return await self._session.get(PlanNode, node_id)

    async def list_by_plan(self, plan_id: str) -> list[PlanNode]:
        stmt = (
            select(PlanNode).where(PlanNode.plan_id == plan_id).order_by(PlanNode.order_index.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_stage(self, plan_id: str, stage_id: str) -> list[PlanNode]:
        stmt = (
            select(PlanNode)
            .where(
                PlanNode.plan_id == plan_id,
                PlanNode.stage_id == stage_id,
            )
            .order_by(PlanNode.order_index.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, node: PlanNode) -> PlanNode:
        self._session.add(node)
        await self._session.commit()
        await self._session.refresh(node)
        return node

    async def update_batch(self, nodes: list[PlanNode]) -> list[PlanNode]:
        for node in nodes:
            self._session.add(node)
        await self._session.commit()
        for node in nodes:
            await self._session.refresh(node)
        return nodes

    async def delete_by_plan(self, plan_id: str) -> None:
        stmt = select(PlanNode).where(PlanNode.plan_id == plan_id)
        result = await self._session.execute(stmt)
        for node in result.scalars().all():
            await self._session.delete(node)
        await self._session.commit()
