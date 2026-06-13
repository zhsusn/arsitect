"""Tests for BypassApprovalService.

Covers DR-017 HITL Bypass Approval Service detailed requirements.
"""

from __future__ import annotations

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.models.bypass_record import BypassRecord
from app.schemas.execution_plan import BypassRequestDTO
from app.services.bypass_approval_service import BypassApprovalService


class FakeBypassRecordRepository:
    """In-memory bypass record repository for unit tests."""

    def __init__(self) -> None:
        self._store: dict[str, BypassRecord] = {}

    async def create(self, record: BypassRecord) -> BypassRecord:
        self._store[record.record_id] = record
        return record

    async def get_by_id(self, record_id: str) -> BypassRecord | None:
        return self._store.get(record_id)

    async def update(self, record: BypassRecord) -> BypassRecord:
        self._store[record.record_id] = record
        return record


class TestBypassApprovalService:
    """BypassApprovalService unit tests."""

    @pytest.fixture
    def repo(self) -> FakeBypassRecordRepository:
        return FakeBypassRecordRepository()

    @pytest.fixture
    def service(self, repo: FakeBypassRecordRepository) -> BypassApprovalService:
        return BypassApprovalService(repo)

    @pytest.fixture
    def valid_dto(self) -> BypassRequestDTO:
        return BypassRequestDTO(
            stage_id="stage-1",
            skill_id="skill-1",
            authorization_token="x" * 32,
            reason="Production hotfix required",
            acknowledged=True,
        )

    @pytest.mark.asyncio
    async def test_request_bypass_success(
        self,
        service: BypassApprovalService,
        valid_dto: BypassRequestDTO,
    ) -> None:
        """TEST-0001: Valid bypass request creates record with PENDING_POST_APPROVAL.

        Covers AC-F-001 / BR-014-1: Emergency bypass creation.
        """
        record = await service.request_bypass(
            dto=valid_dto,
            plan_id="plan-1",
            triggered_by="user-1",
        )
        assert record.status == "PENDING_POST_APPROVAL"
        assert record.plan_id == "plan-1"
        assert record.reason == "Production hotfix required"
        assert record.deadline_at is not None

    @pytest.mark.asyncio
    async def test_request_bypass_invalid_token(
        self,
        service: BypassApprovalService,
        valid_dto: BypassRequestDTO,
    ) -> None:
        """TEST-0002: Token shorter than 32 chars raises ValidationError.

        Covers AC-V-003: Authorization token validation.
        """
        # BypassRequestDTO enforces min_length=32 at schema level,
        # so we test service-level validation with a valid-length token
        # but the service should still reject it.
        # Actually, service validates len < 32, but DTO validates min_length=32.
        # To test service-level rejection we must bypass DTO validation.
        # Use model_construct to bypass Pydantic validation and test service-level check
        dto = BypassRequestDTO.model_construct(
            stage_id="stage-1",
            skill_id="skill-1",
            authorization_token="x" * 31,  # 1 char short for service check
            reason="Production hotfix required",
            acknowledged=True,
        )
        with pytest.raises(ValidationError):
            await service.request_bypass(dto, "plan-1", "user-1")

    @pytest.mark.asyncio
    async def test_request_bypass_not_acknowledged(
        self,
        service: BypassApprovalService,
        valid_dto: BypassRequestDTO,
    ) -> None:
        """TEST-0003: Unacknowledged bypass request raises ValidationError.

        Covers BR-014-2: Explicit acknowledgement required.
        """
        dto = BypassRequestDTO(
            stage_id="stage-1",
            skill_id="skill-1",
            authorization_token="x" * 32,
            reason="Production hotfix required",
            acknowledged=False,
        )
        with pytest.raises(ValidationError):
            await service.request_bypass(dto, "plan-1", "user-1")

    @pytest.mark.asyncio
    async def test_request_bypass_reason_too_short(
        self,
        service: BypassApprovalService,
        valid_dto: BypassRequestDTO,
    ) -> None:
        """TEST-0004: Reason < 5 chars raises ValidationError.

        Covers AC-V-001 / BR-017-5: Bypass reason length validation.
        """
        dto = BypassRequestDTO(
            stage_id="stage-1",
            skill_id="skill-1",
            authorization_token="x" * 32,
            reason="x",
            acknowledged=True,
        )
        with pytest.raises(ValidationError):
            await service.request_bypass(dto, "plan-1", "user-1")

    @pytest.mark.asyncio
    async def test_request_bypass_reason_too_long(
        self,
        service: BypassApprovalService,
        valid_dto: BypassRequestDTO,
    ) -> None:
        """TEST-0005: Reason > 500 chars raises ValidationError.

        Covers AC-V-001 / BR-017-5: Bypass reason length validation.
        """
        dto = BypassRequestDTO(
            stage_id="stage-1",
            skill_id="skill-1",
            authorization_token="x" * 32,
            reason="x" * 501,
            acknowledged=True,
        )
        with pytest.raises(ValidationError):
            await service.request_bypass(dto, "plan-1", "user-1")

    @pytest.mark.asyncio
    async def test_close_bypass_approved(
        self,
        service: BypassApprovalService,
        valid_dto: BypassRequestDTO,
    ) -> None:
        """TEST-0006: APPROVED decision closes bypass record.

        Covers AC-F-008 / BR-014-4: Post-approval closure.
        """
        created = await service.request_bypass(valid_dto, "plan-1", "user-1")
        closed = await service.close_bypass_record(
            created.record_id, "APPROVED"
        )
        assert closed.status == "CLOSED"
        assert closed.closed_at is not None

    @pytest.mark.asyncio
    async def test_close_bypass_rejected(
        self,
        service: BypassApprovalService,
        valid_dto: BypassRequestDTO,
    ) -> None:
        """TEST-0007: REJECTED decision marks violation pending.

        Covers AC-F-009: Rejection leads to violation pending.
        """
        created = await service.request_bypass(valid_dto, "plan-1", "user-1")
        closed = await service.close_bypass_record(
            created.record_id, "REJECTED"
        )
        assert closed.status == "VIOLATION_PENDING"

    @pytest.mark.asyncio
    async def test_close_bypass_timeout(
        self,
        service: BypassApprovalService,
        valid_dto: BypassRequestDTO,
    ) -> None:
        """TEST-0008: TIMEOUT decision marks violation pending.

        Covers AC-F-006 / BR-014-5: Timeout handling.
        """
        created = await service.request_bypass(valid_dto, "plan-1", "user-1")
        closed = await service.close_bypass_record(
            created.record_id, "TIMEOUT"
        )
        assert closed.status == "VIOLATION_PENDING"

    @pytest.mark.asyncio
    async def test_close_bypass_invalid_decision(
        self,
        service: BypassApprovalService,
        valid_dto: BypassRequestDTO,
    ) -> None:
        """TEST-0009: Invalid decision raises ValidationError.

        Covers edge case: unknown decision value.
        """
        created = await service.request_bypass(valid_dto, "plan-1", "user-1")
        with pytest.raises(ValidationError):
            await service.close_bypass_record(created.record_id, "INVALID")

    @pytest.mark.asyncio
    async def test_close_bypass_not_found(
        self,
        service: BypassApprovalService,
    ) -> None:
        """TEST-0010: Closing nonexistent record raises NotFoundError.

        Covers AC-E-002: Record missing simulation.
        """
        with pytest.raises(NotFoundError):
            await service.close_bypass_record("no-such-id", "APPROVED")

    @pytest.mark.asyncio
    async def test_request_bypass_deadline_24h(
        self,
        service: BypassApprovalService,
        valid_dto: BypassRequestDTO,
    ) -> None:
        """TEST-0011: Bypass deadline defaults to 24 hours.

        Covers AC-F-005 / BR-014-4: 24-hour review countdown.
        """
        from datetime import datetime, timedelta

        before = datetime.utcnow()
        record = await service.request_bypass(valid_dto, "plan-1", "user-1")
        after = datetime.utcnow()
        # Allow 5-minute tolerance for test execution time
        assert record.deadline_at >= before + timedelta(hours=23, minutes=55)
        assert record.deadline_at <= after + timedelta(hours=24, minutes=5)
