"""Binding router — data-binding rules."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.schemas.binding import (
    BindingCreateDTO,
    BindingResponseDTO,
    BindingUpdateDTO,
)
from app.services.binding_service import BindingService

router = APIRouter(tags=["bindings"])


@router.post(
    "/projects/{project_id}/binding-rules",
    response_model=BindingResponseDTO,
    status_code=201,
)
async def create_rule(
    project_id: str,
    dto: BindingCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> BindingResponseDTO:
    """Create a new binding rule for a project."""
    svc = BindingService(db)
    rule = await svc.create_rule(
        project_id=project_id,
        source_field=dto.source_field,
        target_field=dto.target_field,
        transform_type=dto.transform_type,
        transform_config=dto.transform_config,
        status=dto.status,
    )
    return BindingResponseDTO(
        rule_id=rule.rule_id,
        project_id=rule.project_id,
        source_field=rule.source_field,
        target_field=rule.target_field,
        transform_type=rule.transform_type,
        transform_config=rule.transform_config,
        status=rule.status,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.get(
    "/projects/{project_id}/binding-rules",
    response_model=list[BindingResponseDTO],
)
async def list_rules(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[BindingResponseDTO]:
    """List binding rules for a project."""
    svc = BindingService(db)
    rules = await svc.list_rules(project_id)
    return [
        BindingResponseDTO(
            rule_id=r.rule_id,
            project_id=r.project_id,
            source_field=r.source_field,
            target_field=r.target_field,
            transform_type=r.transform_type,
            transform_config=r.transform_config,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rules
    ]


@router.get(
    "/binding-rules/{rule_id}",
    response_model=BindingResponseDTO,
)
async def get_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
) -> BindingResponseDTO:
    """Get a single binding rule by ID."""
    svc = BindingService(db)
    rule = await svc.get_rule(rule_id)
    return BindingResponseDTO(
        rule_id=rule.rule_id,
        project_id=rule.project_id,
        source_field=rule.source_field,
        target_field=rule.target_field,
        transform_type=rule.transform_type,
        transform_config=rule.transform_config,
        status=rule.status,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.patch(
    "/binding-rules/{rule_id}",
    response_model=BindingResponseDTO,
)
async def update_rule(
    rule_id: str,
    dto: BindingUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> BindingResponseDTO:
    """Update a binding rule."""
    svc = BindingService(db)
    rule = await svc.update_rule(
        rule_id,
        dto.model_dump(exclude_unset=True),
    )
    return BindingResponseDTO(
        rule_id=rule.rule_id,
        project_id=rule.project_id,
        source_field=rule.source_field,
        target_field=rule.target_field,
        transform_type=rule.transform_type,
        transform_config=rule.transform_config,
        status=rule.status,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.delete(
    "/binding-rules/{rule_id}",
    status_code=204,
    response_model=None,
)
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a binding rule."""
    svc = BindingService(db)
    await svc.delete_rule(rule_id)
