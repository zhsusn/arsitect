"""Template router — template queries and stage management."""

from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.session import get_db
from app.models.project_stage import ProjectStage
from app.models.template_deviation_log import TemplateDeviationLog
from app.schemas.template import (
    ProjectStageDTO,
    StageMergeDTO,
    StageReorderDTO,
    StageSkippableUpdateDTO,
    StageSplitDTO,
    TemplateDetailDTO,
    TemplateDeviationConfirmDTO,
    TemplateDeviationLogDTO,
    TemplateDeviationPreviewDTO,
    TemplateDeviationPreviewRequestDTO,
    TemplateExecutionStrategyResponseDTO,
    TemplateExecutionStrategyUpdateDTO,
    TemplateResponseDTO,
    TemplateStageDTO,
    TemplateStageUpdateDTO,
)
from app.services.impact_scope_calculator import ImpactScopeCalculator
from app.services.stage_config_service import StageConfigService

router = APIRouter(prefix="/templates", tags=["templates"])


# ------------------------------------------------------------------
# Template queries
# ------------------------------------------------------------------
@router.get("", response_model=list[TemplateResponseDTO])
async def list_templates(
    db: AsyncSession = Depends(get_db),
) -> list[TemplateResponseDTO]:
    """List all predefined templates."""
    svc = StageConfigService(db)
    tpls = await svc.list_templates()
    return [TemplateResponseDTO.model_validate(t) for t in tpls]


@router.get("/{level}", response_model=TemplateDetailDTO)
async def get_template(
    level: str,
    db: AsyncSession = Depends(get_db),
) -> TemplateDetailDTO:
    """Get a template with its stage sequence."""
    svc = StageConfigService(db)
    detail = await svc.get_template_detail(level)
    return TemplateDetailDTO(
        template=TemplateResponseDTO.model_validate(detail["template"]),
        stages=[TemplateStageDTO.model_validate(s) for s in detail["stages"]],
    )


@router.put("/{level}/execution-strategy", response_model=TemplateExecutionStrategyResponseDTO)
async def update_template_execution_strategy(
    level: str,
    dto: TemplateExecutionStrategyUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> TemplateExecutionStrategyResponseDTO:
    """Update a template's default execution strategy."""
    svc = StageConfigService(db)
    tpl = await svc.update_execution_strategy(
        level, dto.default_execution_strategy
    )
    return TemplateExecutionStrategyResponseDTO(
        template_id=tpl.template_id,
        default_execution_strategy=tpl.default_execution_strategy,
    )


@router.put("/{level}/stages/{stage_id}", response_model=TemplateStageDTO)
async def update_template_stage(
    level: str,
    stage_id: str,
    dto: TemplateStageUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> TemplateStageDTO:
    """Update skill bindings for a template stage."""
    svc = StageConfigService(db)
    stage = await svc.update_stage(
        stage_id,
        primary_skill_id=dto.primary_skill_id,
        auxiliary_skill_ids=dto.auxiliary_skill_ids,
    )
    return TemplateStageDTO.model_validate(stage)


# ------------------------------------------------------------------
# Project stage sequence (operates on project_stages table)
# ------------------------------------------------------------------
@router.get(
    "/projects/{project_id}/stage-sequence",
    response_model=list[ProjectStageDTO],
)
async def get_stage_sequence(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectStageDTO]:
    """Get the stage sequence for a project."""
    stmt = (
        select(ProjectStage)
        .where(ProjectStage.project_id == project_id)
        .order_by(ProjectStage.order_index)
    )
    result = await db.execute(stmt)
    stages = list(result.scalars().all())
    return [ProjectStageDTO.model_validate(s) for s in stages]


# ------------------------------------------------------------------
# Template deviation preview & confirm
# ------------------------------------------------------------------
@router.post(
    "/projects/{project_id}/template-deviation/preview",
    response_model=TemplateDeviationPreviewDTO,
)
async def preview_template_deviation(
    project_id: str,
    dto: TemplateDeviationPreviewRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> TemplateDeviationPreviewDTO:
    """Preview the impact of switching to a different template."""
    calc = ImpactScopeCalculator(db)
    impact = await calc.calculate_impact(project_id, dto.new_template_id)
    return TemplateDeviationPreviewDTO(
        frozen_count=impact["frozen_count"],
        removed_count=impact["removed_count"],
        added_count=impact["added_count"],
        retained_count=impact["retained_count"],
    )


@router.post(
    "/projects/{project_id}/template-deviation",
    status_code=status.HTTP_200_OK,
)
async def confirm_template_deviation(
    project_id: str,
    dto: TemplateDeviationConfirmDTO,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Confirm and apply template switch."""
    calc = ImpactScopeCalculator(db)
    impact = await calc.calculate_impact(project_id, dto.new_template_id)

    # Freeze executed stages
    for stage in impact["frozen_stages"]:
        if not stage.is_frozen:
            stage.is_frozen = True
            stage.status = "FROZEN"
            db.add(stage)

    # Remove unexecuted stages not in new template
    for stage in impact["removed_stages"]:
        stage.status = "REMOVED"
        db.add(stage)

    # Add new stages from target template
    current_max_order = 0
    if impact["retained_stages"]:
        current_max_order = max(s.order_index for s in impact["retained_stages"])
    for i, tpl_stage in enumerate(impact["added_stages"], start=1):
        ps = ProjectStage(
            project_stage_id=str(uuid.uuid4()),
            project_id=project_id,
            stage_id=tpl_stage.business_stage_key,
            order_index=current_max_order + i,
            status="DEFINED",
            primary_skill_id=tpl_stage.primary_skill_id,
            auxiliary_skill_ids=tpl_stage.auxiliary_skill_ids,
            skippable=tpl_stage.skippable,
            merge_group_id=tpl_stage.merge_group_id,
            is_gate_required=tpl_stage.is_gate_required,
            auto_advance=tpl_stage.auto_advance,
        )
        db.add(ps)

    # Compute stage deviations against the default template for the route.
    stage_svc = StageConfigService(db)
    actual_stage_ids = [s.stage_id for s in impact["retained_stages"] + impact["removed_stages"]]
    deviations = stage_svc.compute_deviations(
        project_id=project_id,
        template_route=dto.new_template_id.lower(),
        actual_stages=actual_stage_ids,
    )

    # Log deviation
    log = TemplateDeviationLog(
        project_id=project_id,
        decision_type="deviation",
        reason=dto.reason,
        details_json=json.dumps(
            {
                "new_template_id": dto.new_template_id,
                "risk_acknowledged": dto.risk_acknowledged,
                "frozen_count": impact["frozen_count"],
                "removed_count": impact["removed_count"],
                "added_count": impact["added_count"],
                "deviation_items": [item.model_dump() for item in dto.deviation_items],
                "stage_deviations": [
                    {
                        "project_id": d.project_id,
                        "template_route": d.template_route,
                        "deviation_type": d.deviation_type,
                        "detail": d.detail,
                    }
                    for d in deviations
                ],
            },
            ensure_ascii=False,
        ),
    )
    db.add(log)

    await db.commit()
    return {
        "frozen": impact["frozen_count"],
        "removed": impact["removed_count"],
        "added": impact["added_count"],
    }


# ------------------------------------------------------------------
# Deviation logs
# ------------------------------------------------------------------
@router.get(
    "/projects/{project_id}/template-deviation-logs",
    response_model=list[TemplateDeviationLogDTO],
)
async def list_deviation_logs(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[TemplateDeviationLogDTO]:
    """List template deviation logs for a project."""
    stmt = (
        select(TemplateDeviationLog)
        .where(TemplateDeviationLog.project_id == project_id)
        .order_by(TemplateDeviationLog.created_at.desc())
    )
    result = await db.execute(stmt)
    logs = list(result.scalars().all())
    return [
        TemplateDeviationLogDTO(
            deviation_id=log.deviation_id,
            project_id=log.project_id,
            decision_type=log.decision_type,
            reason=log.reason,
            details_json=log.details_json,
            operator_id=log.operator_id,
            created_at=log.created_at.isoformat() if log.created_at else None,
        )
        for log in logs
    ]


# ------------------------------------------------------------------
# Project stage management
# ------------------------------------------------------------------
@router.put(
    "/projects/{project_id}/stages/{stage_id}/skippable",
    response_model=ProjectStageDTO,
)
async def update_stage_skippable(
    project_id: str,
    stage_id: str,
    dto: StageSkippableUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> ProjectStageDTO:
    """Update skippable flag for a project stage."""
    stmt = select(ProjectStage).where(
        ProjectStage.project_stage_id == stage_id,
        ProjectStage.project_id == project_id,
    )
    result = await db.execute(stmt)
    stage = result.scalar_one_or_none()
    if stage is None:
        raise NotFoundError(detail=f"Stage '{stage_id}' not found")
    if stage.is_frozen:
        raise ValidationError(detail="Cannot modify a frozen stage")
    stage.skippable = dto.skippable
    await db.commit()
    await db.refresh(stage)
    return ProjectStageDTO.model_validate(stage)


@router.put(
    "/projects/{project_id}/stages/reorder",
    response_model=list[ProjectStageDTO],
)
async def reorder_stages(
    project_id: str,
    dto: StageReorderDTO,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectStageDTO]:
    """Reorder project stages."""
    stage_ids = [s[0] for s in dto.stage_orders]
    stmt = select(ProjectStage).where(
        ProjectStage.project_stage_id.in_(stage_ids),
        ProjectStage.project_id == project_id,
    )
    result = await db.execute(stmt)
    stages = {s.project_stage_id: s for s in result.scalars().all()}

    for stage_id, new_order in dto.stage_orders:
        stage = stages.get(stage_id)
        if stage is None:
            raise NotFoundError(detail=f"Stage '{stage_id}' not found")
        if stage.is_frozen:
            raise ValidationError(detail=f"Stage '{stage_id}' is frozen and cannot be reordered")
        stage.order_index = new_order
        db.add(stage)

    await db.commit()

    # Return reordered sequence
    stmt2 = (
        select(ProjectStage)
        .where(ProjectStage.project_id == project_id)
        .order_by(ProjectStage.order_index)
    )
    result2 = await db.execute(stmt2)
    return [ProjectStageDTO.model_validate(s) for s in result2.scalars().all()]


@router.post(
    "/projects/{project_id}/stages/merge",
    response_model=list[ProjectStageDTO],
)
async def merge_stages(
    project_id: str,
    dto: StageMergeDTO,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectStageDTO]:
    """Merge two adjacent project stages."""
    stmt = (
        select(ProjectStage)
        .where(
            ProjectStage.project_stage_id.in_([dto.source_stage_id, dto.target_stage_id]),
            ProjectStage.project_id == project_id,
        )
        .order_by(ProjectStage.order_index)
    )
    result = await db.execute(stmt)
    stages = list(result.scalars().all())
    if len(stages) != 2:
        raise NotFoundError(detail="One or both stages not found")

    source, target = stages[0], stages[1]
    if source.is_frozen or target.is_frozen:
        raise ValidationError(detail="Cannot merge frozen stages")

    # Mark source as removed, update target name and merge_group
    source.status = "REMOVED"
    target.merge_group_id = target.merge_group_id or str(uuid.uuid4())[:8]
    if dto.new_stage_name:
        # We don't have stage_name on ProjectStage; this would need TemplateStage lookup
        # For MVP we just record the merge_group_id
        pass

    await db.commit()

    stmt2 = (
        select(ProjectStage)
        .where(ProjectStage.project_id == project_id)
        .order_by(ProjectStage.order_index)
    )
    result2 = await db.execute(stmt2)
    return [ProjectStageDTO.model_validate(s) for s in result2.scalars().all()]


@router.post(
    "/projects/{project_id}/stages/split",
    response_model=list[ProjectStageDTO],
)
async def split_stage(
    project_id: str,
    dto: StageSplitDTO,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectStageDTO]:
    """Split a project stage into two."""
    stmt = select(ProjectStage).where(
        ProjectStage.project_stage_id == dto.stage_id,
        ProjectStage.project_id == project_id,
    )
    result = await db.execute(stmt)
    stage = result.scalar_one_or_none()
    if stage is None:
        raise NotFoundError(detail=f"Stage '{dto.stage_id}' not found")
    if stage.is_frozen:
        raise ValidationError(detail="Cannot split a frozen stage")

    # Create a new stage right after the original one
    new_stage = ProjectStage(
        project_stage_id=str(uuid.uuid4()),
        project_id=project_id,
        stage_id=stage.stage_id + "_split",
        order_index=stage.order_index + 1,
        status="DEFINED",
        primary_skill_id=stage.primary_skill_id,
        skippable=stage.skippable,
    )
    db.add(new_stage)

    # Shift later stages
    shift_stmt = (
        select(ProjectStage)
        .where(
            ProjectStage.project_id == project_id,
            ProjectStage.order_index > stage.order_index,
            ProjectStage.project_stage_id != new_stage.project_stage_id,
        )
        .order_by(ProjectStage.order_index)
    )
    shift_result = await db.execute(shift_stmt)
    for s in shift_result.scalars().all():
        s.order_index += 1
        db.add(s)

    await db.commit()

    stmt2 = (
        select(ProjectStage)
        .where(ProjectStage.project_id == project_id)
        .order_by(ProjectStage.order_index)
    )
    result2 = await db.execute(stmt2)
    return [ProjectStageDTO.model_validate(s) for s in result2.scalars().all()]


# ------------------------------------------------------------------
# Freeze template
# ------------------------------------------------------------------
@router.post(
    "/projects/{project_id}/freeze-template",
    status_code=status.HTTP_200_OK,
)
async def freeze_project_template(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Freeze all project stages — called when project transitions to Active."""
    stmt = select(ProjectStage).where(ProjectStage.project_id == project_id)
    result = await db.execute(stmt)
    stages = list(result.scalars().all())
    frozen_count = 0
    for stage in stages:
        if not stage.is_frozen:
            stage.is_frozen = True
            if stage.status not in ("EXECUTED", "FROZEN", "ARCHIVED", "REMOVED"):
                stage.status = "FROZEN"
            db.add(stage)
            frozen_count += 1
    await db.commit()
    return {"frozen_count": frozen_count, "project_id": project_id}
