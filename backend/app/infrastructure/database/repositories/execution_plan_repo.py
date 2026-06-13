"""ExecutionPlan repository with CRUD."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_plan import ExecutionPlan


class ExecutionPlanRepository:
    """Repository for ExecutionPlan entity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, plan: ExecutionPlan) -> ExecutionPlan:
        self._session.add(plan)
        await self._session.commit()
        await self._session.refresh(plan)
        return plan

    async def get_by_id(self, plan_id: str) -> ExecutionPlan | None:
        return await self._session.get(ExecutionPlan, plan_id)

    async def list_by_project(self, project_id: str) -> list[ExecutionPlan]:
        stmt = (
            select(ExecutionPlan)
            .where(ExecutionPlan.project_id == project_id)
            .order_by(ExecutionPlan.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, plan: ExecutionPlan) -> ExecutionPlan:
        self._session.add(plan)
        await self._session.commit()
        await self._session.refresh(plan)
        return plan

    async def delete(self, plan_id: str) -> bool:
        plan = await self.get_by_id(plan_id)
        if plan is None:
            return False
        await self._session.delete(plan)
        await self._session.commit()
        return True
