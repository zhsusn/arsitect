"""Annotation router — create review annotations."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.models.project_stage import ProjectStage
from app.schemas.annotation import AnnotationCreateDTO, AnnotationResponseDTO
from app.services.annotation_service import AnnotationService

router = APIRouter(tags=["annotations"])


@router.post("/annotations", response_model=AnnotationResponseDTO)
async def create_annotation(
    dto: AnnotationCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> AnnotationResponseDTO:
    """Create a new stage annotation.

    If stage_id is not provided, resolves the first project stage
    belonging to the given project_id.
    """
    result = await db.execute(
        select(ProjectStage.project_stage_id)
        .where(ProjectStage.project_id == dto.project_id)
        .limit(1)
    )
    stage_id = result.scalar_one_or_none()
    if stage_id is None:
        from app.core.exceptions import BadRequestError

        raise BadRequestError(
            detail=f"No project stage found for project '{dto.project_id}'"
        )

    svc = AnnotationService(db)
    ann = await svc.create(
        annotation_id=str(uuid.uuid4()),
        stage_id=stage_id,
        author=dto.author,
        content=dto.content,
        annotation_type=dto.annotation_type,
        status="REVIEW_PENDING",
    )
    return AnnotationResponseDTO(
        annotation_id=ann.annotation_id,
        stage_id=ann.stage_id,
        author=ann.author,
        content=ann.content,
        annotation_type=ann.annotation_type,
        status=ann.status,
        created_at=ann.created_at,
    )
