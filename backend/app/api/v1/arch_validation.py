"""ArchValidation router — trigger, diffs, baseline update."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.schemas.arch_validation import (
    ArchValidationBaselineUpdateDTO,
    ArchValidationDiffDTO,
    ArchValidationTriggerDTO,
)
from app.services.arch_validation_service import ArchValidationService

router = APIRouter(tags=["arch-validation"])


@router.post("/projects/{project_id}/arch-validation/trigger", response_model=ArchValidationDiffDTO)
async def trigger_validation(
    project_id: str,
    dto: ArchValidationTriggerDTO,
    db: AsyncSession = Depends(get_db),
) -> ArchValidationDiffDTO:
    """Trigger arch validation for a project level."""
    svc = ArchValidationService(db)
    session = await svc.trigger_validation(project_id, dto.level)
    return ArchValidationDiffDTO(
        session_id=session.session_id,
        project_id=session.project_id,
        level=session.level,
        diff_summary=session.diff_summary,
        status=session.status,
        created_at=session.created_at,
        baseline_dsl=session.baseline_dsl,
        current_dsl=session.current_dsl,
    )


@router.get("/projects/{project_id}/arch-validation/diffs", response_model=list[ArchValidationDiffDTO])
async def get_diffs(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ArchValidationDiffDTO]:
    """Get all validation diffs for a project."""
    svc = ArchValidationService(db)
    sessions = await svc.get_diffs(project_id)
    return [
        ArchValidationDiffDTO(
            session_id=s.session_id,
            project_id=s.project_id,
            level=s.level,
            diff_summary=s.diff_summary,
            status=s.status,
            created_at=s.created_at,
            baseline_dsl=s.baseline_dsl,
            current_dsl=s.current_dsl,
        )
        for s in sessions
    ]


@router.post("/projects/{project_id}/arch-validation/baseline/update", response_model=ArchValidationDiffDTO)
async def update_baseline(
    project_id: str,
    dto: ArchValidationBaselineUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> ArchValidationDiffDTO:
    """Update baseline DSL for a project level."""
    svc = ArchValidationService(db)
    session = await svc.update_baseline(project_id, dto.level)
    return ArchValidationDiffDTO(
        session_id=session.session_id,
        project_id=session.project_id,
        level=session.level,
        diff_summary=session.diff_summary,
        status=session.status,
        created_at=session.created_at,
        baseline_dsl=session.baseline_dsl,
        current_dsl=session.current_dsl,
    )
