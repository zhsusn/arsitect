"""Stage router — detail, skills, executions, artifacts, logs, annotations, gates."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.database.repositories.execution_log_repo import (
    ExecutionLogRepository,
)
from app.infrastructure.database.repositories.skill_execution_repo import (
    SkillExecutionRepository,
)
from app.infrastructure.database.session import get_db
from app.models.project_stage import ProjectStage
from app.models.skill import Skill
from app.models.skill_execution import SkillExecution
from app.schemas.artifact import ArtifactTreeDirectoryDTO
from app.schemas.common import PageResponse
from app.schemas.skill import SkillResponseDTO
from app.schemas.skill_execution import (
    LogEntryDTO,
    LogQueryResultDTO,
    SkillExecutionResponseDTO,
)
from app.schemas.stage_execution_status import StageExecutionStatusDTO
from app.services.annotation_service import AnnotationService
from app.services.artifact_service import ArtifactService
from app.services.stage_detail_service import StageDetailService
from app.services.stage_execution_status_service import StageExecutionStatusService

router = APIRouter(prefix="/stages", tags=["stages"])


# ------------------------------------------------------------------
# Annotation DTOs (existing)
# ------------------------------------------------------------------
class AnnotationCreateDTO(BaseModel):
    """Request body for creating an annotation."""

    annotation_id: str = Field(..., max_length=36)
    author: str = Field(..., max_length=64)
    content: str = Field(..., max_length=2000)
    annotation_type: str = Field(default="comment", max_length=16)
    status: str = Field(default="REVIEW_PENDING", max_length=16)


class AnnotationUpdateDTO(BaseModel):
    """Request body for updating an annotation."""

    content: str = Field(..., max_length=2000)


class AnnotationResponseDTO(BaseModel):
    """Response model for an annotation."""

    model_config = {"from_attributes": True}

    annotation_id: str
    stage_id: str
    author: str
    content: str
    annotation_type: str
    status: str
    viewed_at: str | None


# ------------------------------------------------------------------
# Stage detail
# ------------------------------------------------------------------
@router.get("/{stage_id}")
async def get_stage_detail(
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get aggregated detail for a stage."""
    svc = StageDetailService(db)
    detail = await svc.get_stage_detail(stage_id)
    if detail is None:
        raise NotFoundError(detail=f"Stage '{stage_id}' not found")
    stage = detail["stage"]
    return {
        "project_stage_id": stage.project_stage_id,
        "project_id": stage.project_id,
        "stage_id": stage.stage_id,
        "status": stage.status,
        "order_index": stage.order_index,
        "review_status": detail["review_status"],
        "annotations_count": len(detail["annotations"]),
    }


# ------------------------------------------------------------------
# Skills snapshot
# ------------------------------------------------------------------
@router.get("/{stage_id}/skills", response_model=list[SkillResponseDTO])
async def get_stage_skills(
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[SkillResponseDTO]:
    """Get all skills bound to a stage (primary + execution history)."""
    stage = await db.get(ProjectStage, stage_id)
    if stage is None:
        raise NotFoundError(detail=f"Stage '{stage_id}' not found")

    skill_ids: set[str] = set()
    if stage.primary_skill_id:
        skill_ids.add(stage.primary_skill_id)

    # Also include skills from execution history
    exec_stmt = (
        select(SkillExecution.skill_id).where(SkillExecution.stage_id == stage_id).distinct()
    )
    exec_result = await db.execute(exec_stmt)
    for row in exec_result.scalars().all():
        skill_ids.add(row)

    if not skill_ids:
        return []

    skill_stmt = select(Skill).where(Skill.skill_id.in_(skill_ids))
    skill_result = await db.execute(skill_stmt)
    skills = list(skill_result.scalars().all())
    return [SkillResponseDTO.model_validate(s) for s in skills]


# ------------------------------------------------------------------
# Executions
# ------------------------------------------------------------------
@router.get("/{stage_id}/executions", response_model=list[SkillExecutionResponseDTO])
async def get_stage_executions(
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[SkillExecutionResponseDTO]:
    """Get skill execution records for a stage."""
    stage = await db.get(ProjectStage, stage_id)
    if stage is None:
        raise NotFoundError(detail=f"Stage '{stage_id}' not found")

    repo = SkillExecutionRepository(db)
    executions = await repo.list_by_stage(stage_id)
    return [SkillExecutionResponseDTO.model_validate(e) for e in executions]


@router.get("/{stage_id}/execution-status", response_model=StageExecutionStatusDTO)
async def get_stage_execution_status(
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> StageExecutionStatusDTO:
    """Get aggregated real-time execution status for a stage."""
    svc = StageExecutionStatusService(db)
    status = await svc.get_status(stage_id)
    if status is None:
        raise NotFoundError(detail=f"Stage '{stage_id}' not found")
    return status


# ------------------------------------------------------------------
# Artifacts
# ------------------------------------------------------------------
@router.get("/{stage_id}/artifacts", response_model=list[ArtifactTreeDirectoryDTO])
async def get_stage_artifacts(
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ArtifactTreeDirectoryDTO]:
    """Get artifacts generated for a stage."""
    stage = await db.get(ProjectStage, stage_id)
    if stage is None:
        raise NotFoundError(detail=f"Stage '{stage_id}' not found")

    svc = ArtifactService(db)
    tree = await svc.get_tree(
        stage.project_id,
        filter_stage=stage_id,
    )
    # tree is already list[dict]; Pydantic will validate if we return as DTO
    return [ArtifactTreeDirectoryDTO.model_validate(d) for d in tree]


# ------------------------------------------------------------------
# Logs (aggregated across all executions for the stage)
# ------------------------------------------------------------------
@router.get("/{stage_id}/logs", response_model=LogQueryResultDTO)
async def get_stage_logs(
    stage_id: str,
    keyword: str | None = None,
    level: str = "ALL",
    anchor: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> LogQueryResultDTO:
    """Get aggregated execution logs for a stage."""
    stage = await db.get(ProjectStage, stage_id)
    if stage is None:
        raise NotFoundError(detail=f"Stage '{stage_id}' not found")

    # Find all execution IDs for this stage
    exec_stmt = select(SkillExecution.execution_id).where(SkillExecution.stage_id == stage_id)
    exec_result = await db.execute(exec_stmt)
    execution_ids = list(exec_result.scalars().all())

    if not execution_ids:
        return LogQueryResultDTO(log_entries=[], total_count=0, next_anchor=None)

    repo = ExecutionLogRepository(db)
    log_entries: list[LogEntryDTO] = []
    total_count = 0
    last_anchor: str | None = None

    for exec_id in execution_ids:
        logs = await repo.list_by_execution(
            exec_id,
            level=level if level != "ALL" else None,
            keyword=keyword,
            anchor=anchor,
            limit=100,
        )
        count = await repo.count_by_execution(exec_id)
        total_count += count
        for log in logs:
            log_entries.append(LogEntryDTO.model_validate(log))
            if last_anchor is None or log.log_anchor > last_anchor:
                last_anchor = log.log_anchor

    # Sort by timestamp ascending
    log_entries.sort(key=lambda x: x.timestamp)

    return LogQueryResultDTO(
        log_entries=log_entries,
        total_count=total_count,
        next_anchor=last_anchor,
    )


# ------------------------------------------------------------------
# Annotations (existing)
# ------------------------------------------------------------------
@router.get("/{stage_id}/annotations", response_model=PageResponse[AnnotationResponseDTO])
async def list_annotations(
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> PageResponse[AnnotationResponseDTO]:
    """List annotations for a stage."""
    svc = AnnotationService(db)
    items = await svc.list_by_stage(stage_id)
    return PageResponse[AnnotationResponseDTO](
        data=[AnnotationResponseDTO.model_validate(a) for a in items],
        total_count=len(items),
        page=1,
        page_size=len(items),
        total_pages=1,
        has_next=False,
        has_previous=False,
    )


@router.post(
    "/{stage_id}/annotations",
    response_model=AnnotationResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_annotation(
    stage_id: str,
    dto: AnnotationCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> AnnotationResponseDTO:
    """Create a new annotation on a stage."""
    svc = AnnotationService(db)
    ann = await svc.create(
        annotation_id=dto.annotation_id,
        stage_id=stage_id,
        author=dto.author,
        content=dto.content,
        annotation_type=dto.annotation_type,
        status=dto.status,
    )
    return AnnotationResponseDTO.model_validate(ann)


@router.put("/{stage_id}/annotations/{annotation_id}", response_model=AnnotationResponseDTO)
async def update_annotation(
    stage_id: str,
    annotation_id: str,
    dto: AnnotationUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> AnnotationResponseDTO:
    """Update an existing annotation."""
    svc = AnnotationService(db)
    ann = await svc.update(annotation_id, dto.content)
    if ann is None:
        raise NotFoundError(detail=f"Annotation '{annotation_id}' not found")
    return AnnotationResponseDTO.model_validate(ann)


@router.delete(
    "/{stage_id}/annotations/{annotation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_annotation(
    stage_id: str,
    annotation_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an annotation."""
    svc = AnnotationService(db)
    deleted = await svc.delete(annotation_id)
    if not deleted:
        raise NotFoundError(detail=f"Annotation '{annotation_id}' not found")
