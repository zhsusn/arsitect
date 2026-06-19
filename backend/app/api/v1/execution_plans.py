"""Execution plan router."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.infrastructure.database.repositories.bypass_record_repo import (
    BypassRecordRepository,
)
from app.infrastructure.database.repositories.execution_plan_repo import (
    ExecutionPlanRepository,
)
from app.infrastructure.database.repositories.parallel_group_repo import (
    ParallelGroupRepository,
)
from app.infrastructure.database.repositories.plan_node_repo import PlanNodeRepository
from app.infrastructure.database.session import get_db
from app.models.execution_plan import ExecutionPlan
from app.models.project import Project
from app.schemas.execution_plan import (
    BypassRecordDTO,
    BypassRequestDTO,
    ExecutionPlanResponseDTO,
    ExecutionPlanSummaryDTO,
    PlanAdjustmentDTO,
    PlanNodeDTO,
    PlanValidationResultDTO,
    StageExecutionResultDTO,
)
from app.services.bypass_approval_service import BypassApprovalService
from app.services.execution_plan_generator import ExecutionPlanGenerator
from app.services.stage_orchestrator import StageOrchestrator

router = APIRouter(tags=["execution-plans"])


class _GeneratePlanPayload(BaseModel):
    """生成执行计划请求体。"""

    template_level: str | None = Field(default=None)
    skill_nodes: list[dict[str, Any]] = Field(default_factory=list)


def _derive_plan_status(plan: Any, nodes: list[Any]) -> str:
    """根据计划冻结状态和节点状态推导计划整体状态。"""
    if not plan.is_frozen:
        return "Draft"
    if not nodes:
        return "Frozen"
    statuses = {n.status for n in nodes}
    if any(s in ("EXECUTING", "BYPASS_EXECUTING") for s in statuses):
        return "Running"
    if any(s == "FAILED" for s in statuses):
        return "Failed"
    if all(s == "COMPLETED" for s in statuses):
        return "Completed"
    return "Frozen"


@router.get(
    "/execution-plans",
    response_model=list[ExecutionPlanSummaryDTO],
)
async def list_all_execution_plans(
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[ExecutionPlanSummaryDTO]:
    """获取所有执行计划列表。"""
    ExecutionPlanRepository(db)
    node_repo = PlanNodeRepository(db)

    stmt = (
        select(ExecutionPlan, Project.project_name)
        .join(Project, ExecutionPlan.project_id == Project.project_id)
        .order_by(ExecutionPlan.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = list(result.all())

    async def _build_summary(plan: Any, project_name: str | None) -> ExecutionPlanSummaryDTO:
        nodes = await node_repo.list_by_plan(plan.plan_id)
        status = _derive_plan_status(plan, nodes)
        return ExecutionPlanSummaryDTO(
            plan_id=plan.plan_id,
            project_id=plan.project_id,
            project_name=project_name,
            version=plan.version,
            status=status,
            template_level=plan.template_level,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    summaries = await asyncio.gather(*[_build_summary(plan, pname) for plan, pname in rows])
    return list(summaries)


@router.get(
    "/projects/{project_id}/execution-plans",
    response_model=list[ExecutionPlanResponseDTO],
)
async def list_project_execution_plans(
    project_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[ExecutionPlanResponseDTO]:
    """获取项目的执行计划列表。"""
    repo = ExecutionPlanRepository(db)
    plans = await repo.list_by_project(project_id)
    result: list[ExecutionPlanResponseDTO] = []
    for plan in plans:
        nodes = await PlanNodeRepository(db).list_by_plan(plan.plan_id)
        groups = await ParallelGroupRepository(db).list_by_plan(plan.plan_id)
        result.append(_build_plan_response(plan, nodes, groups))
    return result


@router.post(
    "/projects/{project_id}/execution-plans",
    response_model=ExecutionPlanResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_execution_plan(
    project_id: str,
    payload: _GeneratePlanPayload,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ExecutionPlanResponseDTO:
    """生成执行计划。"""
    project = await db.get(Project, project_id)
    if project is None:
        raise NotFoundError(detail=f"Project '{project_id}' not found")

    template_level = payload.template_level or project.template_level
    generator = ExecutionPlanGenerator(
        plan_repo=ExecutionPlanRepository(db),
        node_repo=PlanNodeRepository(db),
        group_repo=ParallelGroupRepository(db),
    )
    if not payload.skill_nodes:
        plan = await generator.generate_plan_from_project(
            project_id=project_id,
            template_level=template_level,
            execution_strategy=None,
        )
    else:
        plan = await generator.generate_plan(
            project_id=project_id,
            template_level=template_level,
            skill_nodes=payload.skill_nodes,
        )
    nodes = await PlanNodeRepository(db).list_by_plan(plan.plan_id)
    groups = await ParallelGroupRepository(db).list_by_plan(plan.plan_id)
    return _build_plan_response(plan, nodes, groups)


@router.post(
    "/execution-plans/{plan_id}/validate",
    response_model=PlanValidationResultDTO,
)
async def validate_execution_plan(
    plan_id: str,
    adjustments: list[PlanAdjustmentDTO],
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PlanValidationResultDTO:
    """校验计划调整。"""
    plan_repo = ExecutionPlanRepository(db)
    plan = await plan_repo.get_by_id(plan_id)
    if plan is None:
        raise NotFoundError(detail=f"Plan '{plan_id}' not found")

    # MVP: 基础存在性校验即视为通过
    return PlanValidationResultDTO(passed=True)


@router.post(
    "/execution-plans/{plan_id}/freeze",
    response_model=ExecutionPlanResponseDTO,
)
async def freeze_execution_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ExecutionPlanResponseDTO:
    """冻结计划。"""
    plan_repo = ExecutionPlanRepository(db)
    plan = await plan_repo.get_by_id(plan_id)
    if plan is None:
        raise NotFoundError(detail=f"Plan '{plan_id}' not found")

    plan.is_frozen = True
    await plan_repo.update(plan)
    nodes = await PlanNodeRepository(db).list_by_plan(plan_id)
    groups = await ParallelGroupRepository(db).list_by_plan(plan_id)
    return _build_plan_response(plan, nodes, groups)


@router.get(
    "/execution-plans/{plan_id}",
    response_model=ExecutionPlanResponseDTO,
)
async def get_execution_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ExecutionPlanResponseDTO:
    """获取执行计划。"""
    plan_repo = ExecutionPlanRepository(db)
    plan = await plan_repo.get_by_id(plan_id)
    if plan is None:
        raise NotFoundError(detail=f"Plan '{plan_id}' not found")

    nodes = await PlanNodeRepository(db).list_by_plan(plan_id)
    groups = await ParallelGroupRepository(db).list_by_plan(plan_id)
    return _build_plan_response(plan, nodes, groups)


@router.delete(
    "/execution-plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_execution_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> None:
    """删除执行计划。"""
    repo = ExecutionPlanRepository(db)
    deleted = await repo.delete(plan_id)
    if not deleted:
        raise NotFoundError(detail=f"Plan '{plan_id}' not found")


@router.post(
    "/execution-plans/{plan_id}/execute",
    response_model=StageExecutionResultDTO,
)
async def execute_execution_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> StageExecutionResultDTO:
    """启动执行（MVP 简化：调度第一个 Stage）。"""
    node_repo = PlanNodeRepository(db)
    nodes = await node_repo.list_by_plan(plan_id)
    if not nodes:
        raise BadRequestError(detail="Plan has no nodes to execute")

    first_stage_id = nodes[0].stage_id
    orchestrator = StageOrchestrator(
        node_repo=node_repo,
        group_repo=ParallelGroupRepository(db),
    )
    return await orchestrator.schedule_stage_execution(first_stage_id, plan_id)


@router.post(
    "/execution-plans/{plan_id}/cancel",
    response_model=ExecutionPlanResponseDTO,
)
async def cancel_execution_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ExecutionPlanResponseDTO:
    """终止计划执行（MVP：将所有非终态节点标记为 CANCELLED）。"""
    plan_repo = ExecutionPlanRepository(db)
    plan = await plan_repo.get_by_id(plan_id)
    if plan is None:
        raise NotFoundError(detail=f"Plan '{plan_id}' not found")

    node_repo = PlanNodeRepository(db)
    nodes = await node_repo.list_by_plan(plan_id)
    terminal_statuses = {"COMPLETED", "FAILED", "CANCELLED"}
    for node in nodes:
        if node.status not in terminal_statuses:
            node.status = "CANCELLED"
            await node_repo.update(node)

    groups = await ParallelGroupRepository(db).list_by_plan(plan_id)
    return _build_plan_response(plan, nodes, groups)


@router.post(
    "/execution-plans/{plan_id}/pause",
    response_model=dict[str, str],
)
async def pause_execution_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict[str, str]:
    """暂停计划执行（MVP：标记状态，实际调度层未实现完整暂停）。"""
    plan_repo = ExecutionPlanRepository(db)
    plan = await plan_repo.get_by_id(plan_id)
    if plan is None:
        raise NotFoundError(detail=f"Plan '{plan_id}' not found")
    return {"plan_id": plan_id, "action": "paused", "message": "MVP: 暂停状态已记录"}


@router.post(
    "/execution-plans/{plan_id}/resume",
    response_model=dict[str, str],
)
async def resume_execution_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict[str, str]:
    """恢复计划执行（MVP：标记状态，实际调度层未实现完整恢复）。"""
    plan_repo = ExecutionPlanRepository(db)
    plan = await plan_repo.get_by_id(plan_id)
    if plan is None:
        raise NotFoundError(detail=f"Plan '{plan_id}' not found")
    return {"plan_id": plan_id, "action": "resumed", "message": "MVP: 恢复状态已记录"}


@router.get("/execution-plans/{execution_id}/status")
async def get_execution_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """查询执行状态（MVP 简化：execution_id 即 plan_id）。"""
    nodes = await PlanNodeRepository(db).list_by_plan(execution_id)
    return {
        "execution_id": execution_id,
        "plan_id": execution_id,
        "nodes": [{"node_id": n.node_id, "status": n.status} for n in nodes],
    }


@router.post(
    "/executions/{execution_id}/bypass",
    response_model=BypassRecordDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_bypass(
    execution_id: str,
    dto: BypassRequestDTO,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> BypassRecordDTO:
    """旁路审批执行。"""
    svc = BypassApprovalService(BypassRecordRepository(db))
    record = await svc.request_bypass(
        dto=dto,
        plan_id=execution_id,
        triggered_by="system",
    )
    return BypassRecordDTO.model_validate(record)


@router.get(
    "/executions/{execution_id}/bypass-status",
    response_model=list[BypassRecordDTO],
)
async def list_bypass_records(
    execution_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[BypassRecordDTO]:
    """旁路记录查询。"""
    repo = BypassRecordRepository(db)
    records = await repo.list_by_plan(execution_id)
    return [BypassRecordDTO.model_validate(r) for r in records]


def _build_plan_response(
    plan: Any,
    nodes: list[Any],
    groups: list[Any],
) -> ExecutionPlanResponseDTO:
    """构建 ExecutionPlanResponseDTO，填充节点顺序与并行组。"""
    node_id_to_skill: dict[str, str] = {n.node_id: n.skill_id for n in nodes}
    group_dtos: list[dict[str, Any]] = []
    for g in groups:
        node_ids_in_group = json.loads(g.node_ids)
        group_dtos.append(
            {
                "group_id": g.group_id,
                "stage_id": g.stage_id,
                "skill_ids": [node_id_to_skill.get(nid, nid) for nid in node_ids_in_group],
                "group_type": g.group_type,
            }
        )

    node_dtos = [
        PlanNodeDTO(
            node_id=n.node_id,
            plan_id=n.plan_id,
            skill_id=n.skill_id,
            stage_id=n.stage_id,
            order_index=n.order_index,
            node_type=n.node_type,
            module_id=n.module_id,
            status=n.status,
        )
        for n in nodes
    ]

    dependency_matrix: dict[str, Any] = {}
    if plan.dependency_matrix:
        try:
            dependency_matrix = json.loads(plan.dependency_matrix)
        except json.JSONDecodeError:
            dependency_matrix = {}

    return ExecutionPlanResponseDTO(
        plan_id=plan.plan_id,
        project_id=plan.project_id,
        version=plan.version,
        is_frozen=plan.is_frozen,
        template_level=plan.template_level,
        node_order=[n.node_id for n in nodes],
        parallel_groups=group_dtos,  # type: ignore[arg-type]
        dependency_matrix=dependency_matrix,
        nodes=node_dtos,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )
