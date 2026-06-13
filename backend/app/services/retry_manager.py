"""Retry manager for failed skill executions."""

from __future__ import annotations

import uuid

from app.infrastructure.database.repositories.skill_execution_repo import (
    SkillExecutionRepository,
)
from app.models.skill_execution import SkillExecution
from app.schemas.skill_execution import RetryResultDTO


class RetryManager:
    """重试管理器。"""

    def __init__(self, exec_repo: SkillExecutionRepository) -> None:
        """Initialize with execution repository."""
        self._exec_repo = exec_repo

    async def attempt_retry(self, execution_id: str) -> RetryResultDTO:
        """发起重试。

        - 检查原执行存在且 overall_status == FAILED。
        - 检查 retry_count < 3，否则返回 RETRY_LIMIT_EXCEEDED。
        - 创建新的 SkillExecution 记录（trigger_action=RETRY,
          previous_execution_id=原id, retry_count=原count+1）。
        - 返回 new_execution_id。

        Args:
            execution_id: 原执行 ID。

        Returns:
            重试结果 DTO。
        """
        original = await self._exec_repo.get_by_id(execution_id)
        if original is None:
            return RetryResultDTO(
                success=False,
                message="Execution not found",
            )

        if original.overall_status != "FAILED":
            return RetryResultDTO(
                success=False,
                message="Execution is not in FAILED status",
            )

        if original.retry_count >= 3:
            return RetryResultDTO(
                success=False,
                message="Retry limit exceeded",
            )

        new_execution = SkillExecution(
            execution_id=str(uuid.uuid4()),
            project_id=original.project_id,
            stage_id=original.stage_id,
            skill_id=original.skill_id,
            skill_name=original.skill_name,
            trigger_action="RETRY",
            current_phase="NONE",
            phase_status="RUNNING",
            overall_status="NOT_STARTED",
            retry_count=original.retry_count + 1,
            previous_execution_id=original.execution_id,
            is_release_skill=original.is_release_skill,
            release_confirmed=original.release_confirmed,
        )

        created = await self._exec_repo.create(new_execution)
        return RetryResultDTO(
            success=True,
            new_execution_id=created.execution_id,
            message="Retry initiated successfully",
        )
