"""Log collector service for skill execution logs."""

from __future__ import annotations

import uuid

from app.infrastructure.database.repositories.execution_log_repo import (
    ExecutionLogRepository,
)
from app.models.execution_log import ExecutionLog
from app.schemas.skill_execution import (
    LogEntryDTO,
    LogFilterDTO,
    LogQueryResultDTO,
)


class LogCollectorService:
    """调度层日志聚合服务（区别于 pocketflow/log_collector.py 的三阶段日志）。"""

    def __init__(self, repo: ExecutionLogRepository) -> None:
        """Initialize with log repository."""
        self._repo = repo

    async def capture_log(
        self,
        execution_id: str,
        level: str,
        content: str,
    ) -> ExecutionLog:
        """捕获单条日志，自动生成 log_anchor（uuid4 前 16 位）。

        Args:
            execution_id: 执行 ID。
            level: 日志级别。
            content: 日志内容。

        Returns:
            创建的日志记录。
        """
        log = ExecutionLog(
            log_id=str(uuid.uuid4()),
            execution_id=execution_id,
            log_anchor=str(uuid.uuid4())[:16],
            level=level,
            content=content,
        )
        return await self._repo.create(log)

    async def query_logs(
        self,
        execution_id: str,
        filters: LogFilterDTO,
    ) -> LogQueryResultDTO:
        """查询日志，支持关键字搜索、级别过滤、增量拉取。

        Args:
            execution_id: 执行 ID。
            filters: 日志过滤条件。

        Returns:
            日志查询结果 DTO。
        """
        level = filters.level if filters.level != "ALL" else None
        logs = await self._repo.list_by_execution(
            execution_id,
            level=level,
            keyword=filters.keyword,
            anchor=filters.anchor,
            limit=100,
        )
        total = await self._repo.count_by_execution(execution_id)

        log_entries = [LogEntryDTO.model_validate(log) for log in logs]
        next_anchor = logs[-1].log_anchor if logs else None

        return LogQueryResultDTO(
            log_entries=log_entries,
            total_count=total,
            next_anchor=next_anchor,
        )
