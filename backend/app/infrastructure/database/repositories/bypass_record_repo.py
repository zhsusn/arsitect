"""BypassRecord repository with CRUD."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bypass_record import BypassRecord


class BypassRecordRepository:
    """Repository for BypassRecord entity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: BypassRecord) -> BypassRecord:
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def get_by_id(self, record_id: str) -> BypassRecord | None:
        return await self._session.get(BypassRecord, record_id)

    async def list_by_plan(self, plan_id: str) -> list[BypassRecord]:
        stmt = (
            select(BypassRecord)
            .where(BypassRecord.plan_id == plan_id)
            .order_by(BypassRecord.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_pending_overdue(self, now: datetime) -> list[BypassRecord]:
        stmt = (
            select(BypassRecord)
            .where(
                BypassRecord.status == "PENDING_POST_APPROVAL",
                BypassRecord.deadline_at < now,
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, record: BypassRecord) -> BypassRecord:
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def delete(self, record_id: str) -> bool:
        record = await self.get_by_id(record_id)
        if record is None:
            return False
        await self._session.delete(record)
        await self._session.commit()
        return True
