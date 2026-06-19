"""Project router — CRUD and state transition endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.advanced import _get_notification_manager
from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import get_db
from app.models.project import Project
from app.schemas.common import PageResponse
from app.schemas.gate import GateDecisionResponseDTO
from app.schemas.project import (
    BindSizeEstimateDTO,
    OperationLogItemDTO,
    ProjectCreateDTO,
    ProjectExecutionStrategyResponseDTO,
    ProjectExecutionStrategyUpdateDTO,
    ProjectOverviewDTO,
    ProjectResponseDTO,
    ProjectUpdateDTO,
    RiskAlertDTO,
    StageAdvanceResponseDTO,
    StageExecuteResponseDTO,
    StageGateDecisionDTO,
    StageGateDecisionResponseDTO,
    StageProgressDTO,
    StageProgressResponseDTO,
    StageRollbackRequestDTO,
    StageRollbackResponseDTO,
    StageStartResponseDTO,
    TimeboxEntryDTO,
)
from app.services.project_service import ProjectService
from app.services.risk_scanner_service import RiskScannerService
from app.services.stage_gate_controller import StageGateController
from app.services.stage_orchestrator import StageOrchestrator

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
    items, total = await svc.list_projects(app_id, page=page, page_size=page_size)
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
        project_id=dto.project_id or "",
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


@router.put(
    "/projects/{project_id}/execution-strategy",
    response_model=ProjectExecutionStrategyResponseDTO,
)
async def update_project_execution_strategy(
    project_id: str,
    dto: ProjectExecutionStrategyUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Update project execution strategy."""
    svc = ProjectService(db)
    return await svc.update_execution_strategy(
        project_id,
        execution_strategy=dto.execution_strategy,
        reason=dto.reason,
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
    return ProjectOverviewDTO.model_validate(await svc.get_project_overview(project_id))


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
    return [StageProgressDTO.model_validate(s) for s in await svc.list_project_stages(project_id)]


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
    return [OperationLogItemDTO.model_validate(item) for item in await svc.list_operation_logs(project_id, limit=limit)]


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


# Stage orchestration endpoints
@router.post("/projects/{project_id}/start", response_model=StageStartResponseDTO)
async def start_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """启动项目阶段流水线。"""
    orchestrator = StageOrchestrator(session=db)
    return await orchestrator.start_project(project_id)


@router.post(
    "/projects/{project_id}/stages/{stage_id}/execute",
    response_model=StageExecuteResponseDTO,
)
async def execute_project_stage(
    project_id: str,
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """手动触发阶段执行。"""
    orchestrator = StageOrchestrator(session=db)
    return await orchestrator.execute_stage(stage_id)


@router.post(
    "/projects/{project_id}/stages/{stage_id}/advance",
    response_model=StageAdvanceResponseDTO,
)
async def advance_project_stage(
    project_id: str,
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """手动推进到下一阶段。"""
    orchestrator = StageOrchestrator(session=db)
    return await orchestrator.advance_stage(stage_id)


@router.post(
    "/projects/{project_id}/stages/{stage_id}/gate/decide",
    response_model=StageGateDecisionResponseDTO,
)
async def decide_project_stage_gate(
    project_id: str,
    stage_id: str,
    dto: StageGateDecisionDTO,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Gate 决策。"""
    orchestrator = StageOrchestrator(session=db)
    return await orchestrator.decide_gate(stage_id, dto.decision, dto.reason)


@router.get(
    "/projects/{project_id}/stages/{stage_id}/gate",
    response_model=GateDecisionResponseDTO | None,
)
async def get_project_stage_gate(
    project_id: str,
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> GateDecisionResponseDTO | None:
    """获取阶段当前 pending 的 Gate 决策记录。"""
    controller = StageGateController(db)
    gate = await controller.get_pending_gate(stage_id)
    if gate is None:
        return None
    return GateDecisionResponseDTO.model_validate(gate)


@router.get(
    "/projects/{project_id}/stage-progress",
    response_model=StageProgressResponseDTO,
)
async def get_project_stage_progress(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取项目阶段进度与状态。"""
    orchestrator = StageOrchestrator(session=db)
    return await orchestrator.get_stage_progress(project_id)


@router.get("/projects/{project_id}/sse")
async def project_events_stream(
    project_id: str,
    request: Request,
) -> StreamingResponse:
    """SSE event stream for a project."""
    manager = _get_notification_manager()
    return await manager.connect_sse(project_id, request)


@router.post(
    "/projects/{project_id}/stages/{stage_id}/rollback",
    response_model=StageRollbackResponseDTO,
)
async def rollback_project_stage(
    project_id: str,
    stage_id: str,
    dto: StageRollbackRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """回滚到目标阶段并标记下游产物过期。"""
    orchestrator = StageOrchestrator(session=db)
    result = await orchestrator.rollback_stage(
        project_stage_id=stage_id,
        target_stage_id=dto.target_stage_id,
        reason=dto.reason,
        operator_id="system",
    )
    return StageRollbackResponseDTO(**result).model_dump()
