"""ExecutionLog repository with CRUD and filtering."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_log import ExecutionLog


class ExecutionLogRepository:
    """Repository for ExecutionLog entity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, log: ExecutionLog) -> ExecutionLog:
        self._session.add(log)
        await self._session.commit()
        await self._session.refresh(log)
        return log

    async def create_batch(self, logs: list[ExecutionLog]) -> list[ExecutionLog]:
        self._session.add_all(logs)
        await self._session.commit()
        for log in logs:
            await self._session.refresh(log)
        return logs

    async def get_by_id(self, log_id: str) -> ExecutionLog | None:
        return await self._session.get(ExecutionLog, log_id)

    async def list_by_execution(
        self,
        execution_id: str,
        *,
        level: str | None = None,
        keyword: str | None = None,
        anchor: str | None = None,
        limit: int = 100,
    ) -> list[ExecutionLog]:
        stmt = select(ExecutionLog).where(ExecutionLog.execution_id == execution_id)
        if level and level != "ALL":
            stmt = stmt.where(ExecutionLog.level == level)
        if keyword:
            stmt = stmt.where(ExecutionLog.content.contains(keyword))
        if anchor:
            stmt = stmt.where(ExecutionLog.log_anchor > anchor)
        stmt = stmt.order_by(ExecutionLog.log_anchor.asc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_execution(self, execution_id: str) -> int:
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(ExecutionLog)
            .where(ExecutionLog.execution_id == execution_id)
        )
        count = await self._session.scalar(stmt) or 0
        return count

    async def delete_by_execution(self, execution_id: str) -> None:
        stmt = select(ExecutionLog).where(ExecutionLog.execution_id == execution_id)
        result = await self._session.execute(stmt)
        for log in result.scalars().all():
            await self._session.delete(log)
        await self._session.commit()
