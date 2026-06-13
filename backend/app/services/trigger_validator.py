"""Trigger validator for skill execution requests."""

from __future__ import annotations

from app.infrastructure.database.repositories.skill_execution_repo import (
    SkillExecutionRepository,
)
from app.schemas.skill_execution import ExecutionTriggerDTO, TriggerValidationResultDTO


class TriggerValidator:
    """执行触发校验器。"""

    def __init__(self, exec_repo: SkillExecutionRepository) -> None:
        """Initialize with execution repository."""
        self._exec_repo = exec_repo

    async def validate_trigger(
        self,
        dto: ExecutionTriggerDTO,
        skill_name: str,
        is_release_skill: bool,
    ) -> TriggerValidationResultDTO:
        """校验触发条件。

        - SINGLE_EXECUTE: 检查该 skill + stage 是否有 RUNNING 的执行。
        - 发布类 Skill: confirm_release 必须为 True。
        - RETRY: previous_execution_id 必须存在且对应记录 overall_status == FAILED
                 且 retry_count < 3。

        Args:
            dto: 触发请求 DTO。
            skill_name: Skill 名称。
            is_release_skill: 是否为发布类 Skill。

        Returns:
            校验结果 DTO。
        """
        if dto.trigger_action == "SINGLE_EXECUTE":
            running = await self._has_running_execution(
                dto.target_stage_id, skill_name
            )
            if running:
                return TriggerValidationResultDTO(
                    valid=False,
                    error_code="EXECUTION_ALREADY_IN_PROGRESS",
                    message="Execution already in progress for this skill and stage",
                )

        if is_release_skill and not (dto.confirm_release or False):
            return TriggerValidationResultDTO(
                valid=False,
                error_code="RELEASE_CONFIRMATION_REQUIRED",
                message="Release confirmation is required for this skill",
            )

        if dto.trigger_action == "RETRY":
            if not dto.previous_execution_id:
                return TriggerValidationResultDTO(
                    valid=False,
                    error_code="PREVIOUS_EXECUTION_REQUIRED",
                    message="previous_execution_id is required for RETRY",
                )
            prev = await self._exec_repo.get_by_id(dto.previous_execution_id)
            if prev is None:
                return TriggerValidationResultDTO(
                    valid=False,
                    error_code="PREVIOUS_EXECUTION_NOT_FOUND",
                    message="Previous execution not found",
                )
            if prev.overall_status != "FAILED":
                return TriggerValidationResultDTO(
                    valid=False,
                    error_code="PREVIOUS_EXECUTION_NOT_FAILED",
                    message="Previous execution is not in FAILED status",
                )
            if prev.retry_count >= 3:
                return TriggerValidationResultDTO(
                    valid=False,
                    error_code="RETRY_LIMIT_EXCEEDED",
                    message="Retry limit exceeded",
                )

        return TriggerValidationResultDTO(valid=True)

    async def _has_running_execution(
        self, stage_id: str | None, skill_name: str
    ) -> bool:
        """Check if there is a RUNNING execution for the given stage and skill.

        Args:
            stage_id: Stage ID。
            skill_name: Skill 名称。

        Returns:
            True if a running execution exists.
        """
        if stage_id is None:
            return False
        executions = await self._exec_repo.list_by_stage(stage_id)
        return any(
            e.skill_name == skill_name and e.overall_status == "RUNNING"
            for e in executions
        )

    def _is_release_skill(self, skill_name: str) -> bool:
        """判定 Skill 是否为发布相关类型。

        Args:
            skill_name: Skill 名称。

        Returns:
            True if the skill is release-related.
        """
        return skill_name.lower() in {
            "release-management",
            "finish",
            "git-automation",
        }
