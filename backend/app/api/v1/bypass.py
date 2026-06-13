"""Bypass router — apply, list, approve."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.schemas.bypass import (
    BypassApplyDTO,
    BypassApproveDTO,
    BypassResponseDTO,
)
from app.services.bypass_service import BypassService

router = APIRouter(tags=["bypass"])


@router.post("/gates/{gate_id}/bypass", response_model=BypassResponseDTO)
async def apply_bypass(
    gate_id: str,
    dto: BypassApplyDTO,
    db: AsyncSession = Depends(get_db),
) -> BypassResponseDTO:
    """Apply for a bypass approval on a gate."""
    svc = BypassService(db)
    record = await svc.apply_bypass(
        gate_id=gate_id,
        plan_id=dto.plan_id or "",
        stage_id=dto.stage_id,
        skill_id=dto.skill_id,
        triggered_by=dto.triggered_by,
        reason=dto.reason,
        authorizer_token=dto.authorizer_token,
        deadline_hours=dto.deadline_hours,
    )
    return BypassResponseDTO(
        record_id=record.record_id,
        gate_decision_id=record.gate_decision_id,
        plan_id=record.plan_id,
        stage_id=record.stage_id,
        skill_id=record.skill_id,
        triggered_by=record.triggered_by,
        reason=record.reason,
        status=record.status,
        deadline_at=record.deadline_at,
        closed_at=record.closed_at,
        created_at=record.created_at,
    )


@router.get("/gates/{gate_id}/bypass", response_model=BypassResponseDTO | None)
async def get_gate_bypass(
    gate_id: str,
    db: AsyncSession = Depends(get_db),
) -> BypassResponseDTO | None:
    """Get the latest bypass record for a gate."""
    svc = BypassService(db)
    record = await svc.get_latest_for_gate(gate_id)
    if record is None:
        return None

    return BypassResponseDTO(
        record_id=record.record_id,
        gate_decision_id=record.gate_decision_id,
        plan_id=record.plan_id,
        stage_id=record.stage_id,
        skill_id=record.skill_id,
        triggered_by=record.triggered_by,
        reason=record.reason,
        status=record.status,
        deadline_at=record.deadline_at,
        closed_at=record.closed_at,
        created_at=record.created_at,
    )


@router.get("/projects/{project_id}/bypass-applications", response_model=list[BypassResponseDTO])
async def list_bypass_applications(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[BypassResponseDTO]:
    """List bypass applications for a project."""
    svc = BypassService(db)
    records = await svc.list_bypass_applications(project_id)
    return [
        BypassResponseDTO(
            record_id=r.record_id,
            gate_decision_id=r.gate_decision_id,
            plan_id=r.plan_id,
            stage_id=r.stage_id,
            skill_id=r.skill_id,
            triggered_by=r.triggered_by,
            reason=r.reason,
            status=r.status,
            deadline_at=r.deadline_at,
            closed_at=r.closed_at,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.post("/bypass-applications/{record_id}/approve", response_model=BypassResponseDTO)
async def approve_bypass(
    record_id: str,
    dto: BypassApproveDTO,
    db: AsyncSession = Depends(get_db),
) -> BypassResponseDTO:
    """Approve a bypass application."""
    svc = BypassService(db)
    record = await svc.approve_bypass(record_id, dto.approved_by)
    return BypassResponseDTO(
        record_id=record.record_id,
        gate_decision_id=record.gate_decision_id,
        plan_id=record.plan_id,
        stage_id=record.stage_id,
        skill_id=record.skill_id,
        triggered_by=record.triggered_by,
        reason=record.reason,
        status=record.status,
        deadline_at=record.deadline_at,
        closed_at=record.closed_at,
        created_at=record.created_at,
    )
