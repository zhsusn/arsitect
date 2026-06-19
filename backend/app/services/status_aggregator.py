"""Status aggregator for skill execution polling."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.infrastructure.database.repositories.skill_execution_repo import (
    SkillExecutionRepository,
)
from app.models.artifact import ArtifactFile
from app.models.execution_log import ExecutionLog
from app.schemas.skill_execution import (
    ExecutionStatusDTO,
    StageProgressDTO,
)


class StatusAggregator:
    """状态聚合器。"""

    def __init__(self, exec_repo: SkillExecutionRepository) -> None:
        """Initialize with execution repository."""
        self._exec_repo = exec_repo

    async def poll_execution_status(
        self,
        execution_id: str,
        last_anchor: str | None = None,
    ) -> ExecutionStatusDTO:
        """获取执行状态。

        聚合 SkillExecution、关联产物与最近错误日志，返回真实状态。

        Args:
            execution_id: 执行 ID。
            last_anchor: 上次拉取的锚点（预留，当前未使用）。

        Returns:
            执行状态 DTO。

        Raises:
            NotFoundError: 执行记录不存在。
        """
        execution = await self._exec_repo.get_by_id(execution_id)
        if execution is None:
            raise NotFoundError(detail=f"Execution '{execution_id}' not found")

        progress = self._phase_to_percent(execution.current_phase)
        artifact_paths = await self._load_artifact_paths(execution.execution_id)
        error_summary = await self._load_error_summary(execution.execution_id)

        return ExecutionStatusDTO(
            execution_id=execution.execution_id,
            current_phase=execution.current_phase,
            phase_status=execution.phase_status,
            overall_status=execution.overall_status,
            stage_progress_percent=progress,
            status_timestamp=datetime.utcnow(),
            artifact_paths=artifact_paths,
            error_summary=error_summary,
        )

    async def _load_artifact_paths(self, execution_id: str) -> list[str]:
        """Load artifact file paths produced by the execution."""
        session = self._exec_repo._session
        stmt = select(ArtifactFile.file_path).where(ArtifactFile.execution_id == execution_id)
        result = await session.execute(stmt)
        return [row[0] for row in result.all() if row[0]]

    async def _load_error_summary(self, execution_id: str) -> str | None:
        """Load the most recent ERROR log content for the execution."""
        session = self._exec_repo._session
        stmt = (
            select(ExecutionLog.content)
            .where(ExecutionLog.execution_id == execution_id, ExecutionLog.level == "ERROR")
            .order_by(ExecutionLog.timestamp.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        return row if row else None

    async def calculate_stage_progress(
        self,
        execution_id: str,
    ) -> StageProgressDTO:
        """计算 Stage 进度百分比。

        MVP 简化：PREP=33, EXEC=66, POST=90, COMPLETED=100, NONE=0。

        Args:
            execution_id: 执行 ID。

        Returns:
            Stage 进度 DTO。

        Raises:
            NotFoundError: 执行记录不存在。
        """
        execution = await self._exec_repo.get_by_id(execution_id)
        if execution is None:
            raise NotFoundError(detail=f"Execution '{execution_id}' not found")

        percent = self._phase_to_percent(execution.current_phase)
        return StageProgressDTO(
            execution_id=execution_id,
            stage_progress_percent=percent,
            estimated_remaining_seconds=None,
        )

    @staticmethod
    def _phase_to_percent(phase: str) -> int:
        """Map execution phase to progress percentage.

        Args:
            phase: Current phase string.

        Returns:
            Progress percentage.
        """
        mapping = {
            "NONE": 0,
            "PREP": 33,
            "EXEC": 66,
            "POST": 90,
            "COMPLETED": 100,
        }
        return mapping.get(phase, 0)
