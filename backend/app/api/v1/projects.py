"""Project router — CRUD and state transition endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import get_db
from app.models.project import Project
from app.schemas.common import PageResponse
from app.schemas.project import (
    BindSizeEstimateDTO,
    OperationLogItemDTO,
    ProjectCreateDTO,
    ProjectOverviewDTO,
    ProjectResponseDTO,
    ProjectUpdateDTO,
    RiskAlertDTO,
    StageProgressDTO,
    TimeboxEntryDTO,
)
from app.services.project_service import ProjectService
from app.services.risk_scanner_service import RiskScannerService

router = APIRouter(tags=["projects"])


# List / Create under application
@router.get(
    "/applications/{app_id}/projects",
    response_model=PageResponse[ProjectResponseDTO],
)
async def list_projects(
    app_id: str,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
) -> PageResponse[ProjectResponseDTO]:
    """List projects under an application with pagination."""
    svc = ProjectService(db)
    items, total = await svc.list_projects(
        app_id, page=page, page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size
    return PageResponse[ProjectResponseDTO](
        data=[ProjectResponseDTO.model_validate(p) for p in items],
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.post(
    "/applications/{app_id}/projects",
    response_model=ProjectResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    app_id: str,
    dto: ProjectCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Create a new project under an application."""
    svc = ProjectService(db)
    return await svc.create_project(
        project_id=dto.project_id,
        project_name=dto.project_name,
        application_id=app_id,
        template_level=dto.template_level,
        project_description=dto.project_description,
    )


# Single project operations
@router.get("/projects/{project_id}", response_model=ProjectResponseDTO)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Get project details."""
    svc = ProjectService(db)
    return await svc.get_project(project_id)


@router.patch("/projects/{project_id}", response_model=ProjectResponseDTO)
async def update_project(
    project_id: str,
    dto: ProjectUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Update project info."""
    svc = ProjectService(db)
    return await svc.update_project(
        project_id,
        project_name=dto.project_name,
        project_description=dto.project_description,
    )


@router.post("/projects/{project_id}/archive")
async def archive_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Archive a project."""
    svc = ProjectService(db)
    await svc.archive_project(project_id)
    return {"status": "archived", "project_id": project_id}


@router.post("/projects/{project_id}/activate", response_model=ProjectResponseDTO)
async def activate_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Activate (confirm) a project."""
    svc = ProjectService(db)
    return await svc.activate_project(project_id)


@router.post("/projects/{project_id}/cancel", response_model=ProjectResponseDTO)
async def cancel_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Cancel a project."""
    svc = ProjectService(db)
    return await svc.cancel_project(project_id)


# Risk alerts
@router.get(
    "/projects/{project_id}/risk-alerts",
    response_model=list[RiskAlertDTO],
)
async def list_project_risk_alerts(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[RiskAlertDTO]:
    """Get risk alerts for a project."""
    svc = ProjectService(db)
    proj = await svc.get_project(project_id)
    rs = RiskScannerService(db)
    alerts = await rs.scan_project(proj)
    return [
        RiskAlertDTO(
            alert_type=a.alert_type,
            severity=a.severity,
            message=a.message,
            project_id=a.project_id,
            stage_id=a.stage_id,
        )
        for a in alerts
    ]


# Timebox
@router.get(
    "/projects/{project_id}/timebox",
    response_model=list[TimeboxEntryDTO],
)
async def get_timebox(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[TimeboxEntryDTO]:
    """Get timebox configuration for a project (placeholder)."""
    svc = ProjectService(db)
    proj = await svc.get_project(project_id)
    if proj is None:
        raise NotFoundError(detail=f"Project '{project_id}' not found")
    # MVP: return empty list or mock data
    return []


# Project overview (detail drawer)
@router.get(
    "/projects/{project_id}/overview",
    response_model=ProjectOverviewDTO,
)
async def get_project_overview(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectOverviewDTO:
    """Get aggregated project overview for detail drawer."""
    svc = ProjectService(db)
    return await svc.get_project_overview(project_id)


# Stage progress
@router.get(
    "/projects/{project_id}/stages",
    response_model=list[StageProgressDTO],
)
async def list_project_stages(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[StageProgressDTO]:
    """List stage progress for a project."""
    svc = ProjectService(db)
    return await svc.list_project_stages(project_id)


# Operation logs
@router.get(
    "/projects/{project_id}/operation-logs",
    response_model=list[OperationLogItemDTO],
)
async def list_project_operation_logs(
    project_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[OperationLogItemDTO]:
    """List recent operation logs for a project."""
    svc = ProjectService(db)
    return await svc.list_operation_logs(project_id, limit=limit)


# Bind size estimate
@router.patch("/projects/{project_id}/size-estimate")
async def bind_size_estimate(
    project_id: str,
    dto: BindSizeEstimateDTO,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Bind or unbind a size estimate to/from a project."""
    svc = ProjectService(db)
    await svc.bind_size_estimate(project_id, dto.estimate_id)
    return {"status": "ok", "project_id": project_id}
