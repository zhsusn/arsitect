"""Complexity router — size estimates and template recommendations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.schemas.complexity import (
    ComplexityAssessInputDTO,
    ComplexityAssessResultDTO,
    ComplexityTemplateDTO,
    PathDecisionCreateDTO,
    PathDecisionResponseDTO,
    SizeEstimateCreateDTO,
    SizeEstimateResponseDTO,
)
from app.services.complexity_service import ComplexityService

router = APIRouter(tags=["complexity"])

# In-memory decision log storage for MVP
_decision_logs: list[dict[str, str | None]] = []


@router.post(
    "/complexity/assess",
    response_model=ComplexityAssessResultDTO,
)
async def assess_complexity(dto: ComplexityAssessInputDTO) -> ComplexityAssessResultDTO:
    """Assess project complexity from five numeric dimensions."""
    result: dict[str, Any] = ComplexityService.assess(
        module_count=dto.module_count,
        interface_complexity=dto.interface_complexity,
        page_count=dto.page_count,
        entity_count=dto.entity_count,
        integration_count=dto.integration_count,
    )
    return ComplexityAssessResultDTO(
        optimistic_score=int(result["optimistic_score"]),
        expected_score=int(result["expected_score"]),
        conservative_score=int(result["conservative_score"]),
        complexity_level=str(result["complexity_level"]),
        route=result.get("route"),
        confidence=result.get("confidence"),
        reasoning=result.get("reasoning"),
        radar_values=result.get("radar_values"),
    )


@router.get(
    "/complexity/templates",
    response_model=list[ComplexityTemplateDTO],
)
async def list_all_templates() -> list[ComplexityTemplateDTO]:
    """List all complexity template recommendations."""
    levels = ["Trivial", "Light", "Standard", "Deep"]
    results: list[ComplexityTemplateDTO] = []
    for level in levels:
        data = ComplexityService.get_template_recommendation(level)
        results.append(
            ComplexityTemplateDTO(
                level=str(data["level"]),
                label=str(data["label"]),
                recommended_template=str(data["recommended_template"]),
                description=str(data["description"]),
                stage_count=int(data["stage_count"]),
                estimated_skill_count=int(data["estimated_skill_count"]),
            )
        )
    return results


@router.post(
    "/projects/{project_id}/size-estimates",
    response_model=SizeEstimateResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_size_estimate(
    project_id: str,
    dto: SizeEstimateCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> SizeEstimateResponseDTO:
    """Create a size estimate for a project."""
    svc = ComplexityService(db)
    estimate = await svc.create_size_estimate(
        project_id=project_id,
        module_count=dto.module_count,
        interface_count=dto.interface_count,
        page_count=dto.page_count,
        tech_complexity=dto.tech_complexity,
        risk_level=dto.risk_level,
    )
    return SizeEstimateResponseDTO.model_validate(estimate)


@router.get(
    "/projects/{project_id}/size-estimates",
    response_model=list[SizeEstimateResponseDTO],
)
async def list_size_estimates(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[SizeEstimateResponseDTO]:
    """List size estimates for a project."""
    svc = ComplexityService(db)
    items = await svc.list_size_estimates(project_id)
    return [SizeEstimateResponseDTO.model_validate(e) for e in items]


@router.get(
    "/complexity/templates/{level}",
    response_model=ComplexityTemplateDTO,
)
async def get_template_recommendation(level: str) -> ComplexityTemplateDTO:
    """Get template recommendation for a complexity level."""
    data = ComplexityService.get_template_recommendation(level)
    return ComplexityTemplateDTO(
        level=str(data["level"]),
        label=str(data["label"]),
        recommended_template=str(data["recommended_template"]),
        description=str(data["description"]),
        stage_count=int(data["stage_count"]),
        estimated_skill_count=int(data["estimated_skill_count"]),
    )


@router.post(
    "/complexity/decisions",
    response_model=PathDecisionResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_decision(dto: PathDecisionCreateDTO) -> PathDecisionResponseDTO:
    """Create a path decision log entry."""
    decision: dict[str, str | None] = {
        "decision_id": str(uuid.uuid4()),
        "project_id": dto.project_id,
        "decision_type": dto.decision_type,
        "from_path": dto.from_path,
        "to_path": dto.to_path,
        "reason": dto.reason,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _decision_logs.insert(0, decision)
    return PathDecisionResponseDTO.model_validate(decision)


@router.get(
    "/complexity/decisions",
    response_model=list[PathDecisionResponseDTO],
)
async def list_decisions(project_id: str | None = None) -> list[PathDecisionResponseDTO]:
    """List path decision log entries."""
    items = _decision_logs
    if project_id:
        items = [d for d in items if d.get("project_id") == project_id]
    return [PathDecisionResponseDTO.model_validate(d) for d in items]
