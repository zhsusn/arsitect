"""Monitoring router — overview, project stats, operation logs."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.schemas.monitoring import (
    MonitoringOverviewDTO,
    OperationLogDTO,
    OperationLogListDTO,
    ProjectStatsDTO,
)
from app.services.monitoring_service import MonitoringService

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/overview", response_model=MonitoringOverviewDTO)
async def get_overview(
    db: AsyncSession = Depends(get_db),
) -> MonitoringOverviewDTO:
    """Get global monitoring overview."""
    svc = MonitoringService(db)
    data = await svc.get_overview()
    return MonitoringOverviewDTO(**data)


@router.get("/projects/{project_id}/stats", response_model=ProjectStatsDTO)
async def get_project_stats(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectStatsDTO:
    """Get per-project monitoring stats."""
    svc = MonitoringService(db)
    data = await svc.get_project_stats(project_id)
    return ProjectStatsDTO(**data)


@router.get("/projects/{project_id}/operation-logs", response_model=OperationLogListDTO)
async def list_operation_logs(
    project_id: str,
    action: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> OperationLogListDTO:
    """List operation logs for a project."""
    svc = MonitoringService(db)
    logs, total = await svc.list_operation_logs(
        project_id, action=action, limit=limit, offset=offset
    )
    return OperationLogListDTO(
        logs=[
            OperationLogDTO(
                log_id=log.log_id,
                project_id=log.project_id,
                operator_id=log.operator_id,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                detail=log.detail,
                created_at=log.created_at,
            )
            for log in logs
        ],
        total=total,
    )
