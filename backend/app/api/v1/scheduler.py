"""Scheduler router — DAG execution and gate approvals."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.event_bus import get_event_bus
from app.common.project_context import ProjectContext
from app.core.exceptions import BadRequestError, NotFoundError
from app.engine.pocketflow_engine import KimiCLIAdapter, PocketFlowEngine
from app.infrastructure.database.repositories.execution_plan_repo import (
    ExecutionPlanRepository,
)
from app.infrastructure.database.repositories.gate_repo import GateRepository
from app.infrastructure.database.session import get_db
from app.scheduler.dag_scheduler import DAGDefinition, DAGScheduler
from app.scheduler.gate_controller import GateController
from app.scheduler.state_machine import StateMachineManager
from app.schemas.bypass import BypassApplyDTO, BypassResponseDTO
from app.schemas.common import PageResponse
from app.schemas.gate import (
    GateDecisionResponseDTO,
    GateRejectRequestDTO,
    GateSelfCheckResponseDTO,
)
from app.services.bypass_service import BypassService

router = APIRouter(tags=["scheduler"])


class DAGExecuteRequest(BaseModel):
    """Request body for executing a YAML DAG."""

    yaml_content: str = Field(..., description="YAML DAG definition")
    project_id: str = Field(..., description="Project ID")


class DAGExecuteResponse(BaseModel):
    """Response for DAG execute endpoint."""

    dag_id: str
    layers: int


async def _execute_dag_async(dag: DAGDefinition) -> None:
    """Background task to execute a DAG."""
    engine = PocketFlowEngine(
        KimiCLIAdapter(),
        ProjectContext(dag.project_id),
    )
    state_machine = StateMachineManager(None, get_event_bus())
    scheduler = DAGScheduler(engine, state_machine)
    await scheduler.execute(dag)


@router.post("/scheduler/dag/execute", response_model=DAGExecuteResponse)
async def execute_dag(
    request: DAGExecuteRequest,
    background_tasks: BackgroundTasks,
) -> DAGExecuteResponse:
    """Parse YAML and execute a DAG in the background."""
    dag = DAGScheduler.parse_yaml(request.yaml_content, request.project_id)
    background_tasks.add_task(_execute_dag_async, dag)
    return DAGExecuteResponse(
        dag_id=request.project_id,
        layers=len(dag.topological_layers()),
    )


# ============================================================
# Gate approvals
# ============================================================
def _build_gate_controller(
    db: AsyncSession,
) -> GateController:
    """Build a GateController with state machine and event bus."""
    state_machine = StateMachineManager(db, get_event_bus())
    return GateController(state_machine, get_event_bus(), db)


@router.get("/gates/pending", response_model=list[dict[str, Any]])
async def get_pending_gates(
    project_id: str | None = Query(None, description="Project ID"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get pending gate queue."""
    controller = _build_gate_controller(db)
    gates = controller.get_pending_gates(project_id)
    return [
        {
            "gate_id": g.gate_id,
            "skill_id": g.skill_id,
            "project_id": g.project_id,
            "summary": g.summary,
            "created_at": g.created_at.isoformat(),
        }
        for g in gates
    ]


@router.get("/gates", response_model=PageResponse[GateDecisionResponseDTO])
async def list_gates(
    project_id: str = Query(..., description="Project ID"),
    gate_type: str | None = Query(None, description="Gate type filter"),
    status: str | None = Query(None, description="Status filter"),
    sort_by: str | None = Query(None, description="Sort field"),
    sort_order: str | None = Query(None, description="Sort order"),
    db: AsyncSession = Depends(get_db),
) -> PageResponse[GateDecisionResponseDTO]:
    """List persisted gate decisions for a project."""
    repo = GateRepository(db)
    items, total = await repo.list_by_project(
        project_id,
        gate_type=gate_type,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    page = 1
    page_size = 50
    total_pages = (total + page_size - 1) // page_size
    return PageResponse[GateDecisionResponseDTO](
        data=[GateDecisionResponseDTO.model_validate(g) for g in items],
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.get("/gates/{gate_id}", response_model=GateDecisionResponseDTO)
async def get_gate(
    gate_id: str,
    db: AsyncSession = Depends(get_db),
) -> GateDecisionResponseDTO:
    """Get a gate decision by ID."""
    repo = GateRepository(db)
    gate = await repo.get_by_id(gate_id)
    if gate is None:
        raise NotFoundError(detail=f"Gate '{gate_id}' not found")
    return GateDecisionResponseDTO.model_validate(gate)


@router.post("/gates/{gate_id}/approve", response_model=GateDecisionResponseDTO)
async def approve_gate(
    gate_id: str,
    db: AsyncSession = Depends(get_db),
) -> GateDecisionResponseDTO:
    """Approve a gate."""
    controller = _build_gate_controller(db)
    await controller.approve(gate_id, "system", "")
    return await get_gate(gate_id, db)


@router.post("/gates/{gate_id}/reject", response_model=GateDecisionResponseDTO)
async def reject_gate(
    gate_id: str,
    dto: GateRejectRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> GateDecisionResponseDTO:
    """Reject a gate."""
    if len(dto.reason) < 5 or len(dto.reason) > 500:
        raise BadRequestError(detail="Reason must be between 5 and 500 characters")
    controller = _build_gate_controller(db)
    await controller.reject(gate_id, "system", dto.reason)
    return await get_gate(gate_id, db)


@router.post("/gates/{gate_id}/retry", response_model=GateDecisionResponseDTO)
async def retry_gate(
    gate_id: str,
    db: AsyncSession = Depends(get_db),
) -> GateDecisionResponseDTO:
    """Retry a gate (reset to pending)."""
    controller = _build_gate_controller(db)
    await controller.retry(gate_id, "system", "")
    return await get_gate(gate_id, db)


@router.get("/gates/history", response_model=PageResponse[GateDecisionResponseDTO])
async def get_gate_history(
    project_id: str = Query(..., description="Project ID"),
    gate_type: str | None = Query(None, description="Gate type filter"),
    decision_type: str | None = Query(None, description="Decision type filter"),
    db: AsyncSession = Depends(get_db),
) -> PageResponse[GateDecisionResponseDTO]:
    """List resolved gate decisions as history for a project."""
    repo = GateRepository(db)
    items, total = await repo.list_by_project(
        project_id,
        gate_type=gate_type,
        status=None,
        sort_by="created_at",
        sort_order="desc",
    )
    if decision_type:
        items = [g for g in items if g.decision_type == decision_type]

    page = 1
    page_size = 50
    total_pages = (total + page_size - 1) // page_size
    return PageResponse[GateDecisionResponseDTO](
        data=[GateDecisionResponseDTO.model_validate(g) for g in items],
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.get("/gates/{gate_id}/self-check", response_model=GateSelfCheckResponseDTO)
async def get_gate_self_check(
    gate_id: str,
    db: AsyncSession = Depends(get_db),
) -> GateSelfCheckResponseDTO:
    """Return a lightweight self-check summary for a gate decision."""
    repo = GateRepository(db)
    gate = await repo.get_by_id(gate_id)
    if gate is None:
        raise NotFoundError(detail=f"Gate '{gate_id}' not found")

    status_to_confidence = {
        "passed": "high",
        "bypassed": "medium",
        "rejected": "low",
        "pending": "unknown",
    }
    status_to_quality = {
        "passed": "passed",
        "bypassed": "conditional",
        "rejected": "failed",
        "pending": "pending",
    }
    status_to_risk = {
        "passed": "low",
        "bypassed": "medium",
        "rejected": "high",
        "pending": "unknown",
    }

    return GateSelfCheckResponseDTO(
        confidence=status_to_confidence.get(gate.status, "unknown"),
        artifact_integrity="ok" if gate.status in {"passed", "bypassed"} else "check_needed",
        quality_gate=status_to_quality.get(gate.status, "pending"),
        risk_level=status_to_risk.get(gate.status, "unknown"),
        artifact_count=1,
        required_artifacts=1,
    )


@router.post("/gates/{gate_id}/bypass", response_model=BypassResponseDTO)
async def bypass_gate(
    gate_id: str,
    dto: BypassApplyDTO,
    db: AsyncSession = Depends(get_db),
) -> BypassResponseDTO:
    """Apply for a bypass on a gate.

    Migrates the legacy bypass flow into the Batch-03 gate controller.
    """
    repo = GateRepository(db)
    gate = await repo.get_by_id(gate_id)

    plan_id = dto.plan_id
    if not plan_id:
        if gate is None:
            raise NotFoundError(detail=f"Gate '{gate_id}' not found")
        plans = await ExecutionPlanRepository(db).list_by_project(gate.project_id)
        if plans:
            plan_id = plans[0].plan_id
        else:
            raise BadRequestError(detail=f"No execution plan found for project '{gate.project_id}'")

    bypass_record = await BypassService(db).apply_bypass(
        gate_id=gate_id,
        plan_id=plan_id,
        stage_id=dto.stage_id,
        skill_id=dto.skill_id,
        triggered_by=dto.triggered_by,
        reason=dto.reason,
        authorizer_token=dto.authorizer_token,
        deadline_hours=dto.deadline_hours,
    )

    controller = _build_gate_controller(db)
    await controller.bypass(gate_id, dto.triggered_by, dto.reason)

    return BypassResponseDTO(
        record_id=bypass_record.record_id,
        gate_decision_id=bypass_record.gate_decision_id,
        plan_id=bypass_record.plan_id,
        stage_id=bypass_record.stage_id,
        skill_id=bypass_record.skill_id,
        triggered_by=bypass_record.triggered_by,
        reason=bypass_record.reason,
        status=bypass_record.status,
        deadline_at=bypass_record.deadline_at,
        closed_at=bypass_record.closed_at,
        created_at=bypass_record.created_at,
    )
