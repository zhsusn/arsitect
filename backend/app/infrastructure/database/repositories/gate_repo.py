"""Gate repository with CRUD and filtering."""

from __future__ import annotations

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gate_decision import GateDecision


class GateRepository:
    """Repository for GateDecision entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def create(self, gate: GateDecision) -> GateDecision:
        """Create a new gate decision record."""
        self._session.add(gate)
        await self._session.commit()
        await self._session.refresh(gate)
        return gate

    async def get_by_id(self, decision_id: str) -> GateDecision | None:
        """Fetch a gate decision by its primary key."""
        return await self._session.get(GateDecision, decision_id)

    async def list_by_project(
        self,
        project_id: str,
        *,
        gate_type: str | None = None,
        status: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> tuple[list[GateDecision], int]:
        """List gate decisions by project ID with optional filters."""
        stmt = select(GateDecision).where(GateDecision.project_id == project_id)

        if gate_type is not None:
            stmt = stmt.where(GateDecision.gate_type == gate_type)
        if status is not None:
            stmt = stmt.where(GateDecision.status == status)

        if sort_by is not None:
            order = desc if sort_order == "desc" else asc
            if sort_by == "created_at":
                stmt = stmt.order_by(order(GateDecision.created_at))
            elif sort_by == "updated_at":
                stmt = stmt.order_by(order(GateDecision.updated_at))
            elif sort_by == "status":
                stmt = stmt.order_by(order(GateDecision.status))
            else:
                stmt = stmt.order_by(order(GateDecision.created_at))
        else:
            stmt = stmt.order_by(desc(GateDecision.created_at))

        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        count_stmt = (
            select(func.count())
            .select_from(GateDecision)
            .where(GateDecision.project_id == project_id)
        )
        if gate_type is not None:
            count_stmt = count_stmt.where(GateDecision.gate_type == gate_type)
        if status is not None:
            count_stmt = count_stmt.where(GateDecision.status == status)

        total = await self._session.scalar(count_stmt) or 0
        return items, total

    async def update(self, gate: GateDecision) -> GateDecision:
        """Update an existing gate decision."""
        self._session.add(gate)
        await self._session.commit()
        await self._session.refresh(gate)
        return gate
