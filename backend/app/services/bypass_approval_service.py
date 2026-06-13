"""Bypass approval service."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.repositories.bypass_record_repo import (
    BypassRecordRepository,
)
from app.models.bypass_record import BypassRecord
from app.schemas.execution_plan import BypassRequestDTO


class BypassApprovalService:
    """旁路审批服务。"""

    def __init__(self, repo: BypassRecordRepository) -> None:
        """Initialize with repository."""
        self._repo = repo

    async def request_bypass(
        self,
        dto: BypassRequestDTO,
        plan_id: str,
        triggered_by: str,
    ) -> BypassRecord:
        """校验授权令牌，创建旁路审批记录，启动 24h 倒计时。

        Args:
            dto: 旁路审批请求 DTO。
            plan_id: 计划 ID。
            triggered_by: 触发者 ID。

        Returns:
            创建的旁路审批记录。

        Raises:
            ValidationError: 校验失败时抛出。
        """
        if not dto.authorization_token or len(dto.authorization_token) < 32:
            raise ValidationError(detail="授权令牌无效")

        if not dto.acknowledged:
            raise ValidationError(detail="BYPASS_NOT_ACKNOWLEDGED")

        if len(dto.reason) < 5 or len(dto.reason) > 500:
            raise ValidationError(detail="旁路理由长度必须在 5-500 字符之间")

        record = BypassRecord(
            record_id=str(uuid.uuid4()),
            plan_id=plan_id,
            stage_id=dto.stage_id,
            skill_id=dto.skill_id,
            triggered_by=triggered_by,
            authorizer_token=dto.authorization_token,
            reason=dto.reason,
            status="PENDING_POST_APPROVAL",
            deadline_at=datetime.utcnow() + timedelta(hours=24),
        )
        return await self._repo.create(record)

    async def close_bypass_record(
        self,
        record_id: str,
        decision: str,
    ) -> BypassRecord:
        """补审批闭环。

        Args:
            record_id: 记录 ID。
            decision: 决策结果 (APPROVED | REJECTED | TIMEOUT)。

        Returns:
            更新后的旁路审批记录。

        Raises:
            NotFoundError: 记录不存在时抛出。
        """
        record = await self._repo.get_by_id(record_id)
        if record is None:
            raise NotFoundError(detail=f"Bypass record '{record_id}' not found")

        if decision == "APPROVED":
            record.status = "CLOSED"
        elif decision in ("REJECTED", "TIMEOUT"):
            record.status = "VIOLATION_PENDING"
        else:
            raise ValidationError(detail=f"Invalid decision '{decision}'")

        record.closed_at = datetime.utcnow()
        return await self._repo.update(record)
