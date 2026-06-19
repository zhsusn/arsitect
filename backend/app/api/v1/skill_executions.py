"""Skill execution router — trigger, status, logs, retry, confirm."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
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
from app.schemas.skill_execution import (
    ExecutionStatusDTO,
    ExecutionTriggerDTO,
    LogFilterDTO,
    LogQueryResultDTO,
    RetryResultDTO,
    SkillExecutionResponseDTO,
)
from app.services.log_collector_service import LogCollectorService
from app.services.retry_manager import RetryManager
from app.services.status_aggregator import StatusAggregator
from app.services.trigger_validator import TriggerValidator

router = APIRouter(prefix="/executions", tags=["skill-executions"])


async def _resolve_skill(db: AsyncSession, skill_name: str | None) -> Skill:
    """Resolve skill by name or ID.

    Args:
        db: Database session.
        skill_name: Skill name or skill ID.

    Returns:
        Skill ORM model.

    Raises:
        BadRequestError: skill_name is missing.
        NotFoundError: Skill not found.
    """
    if skill_name is None:
        raise BadRequestError(detail="target_skill_name is required")
    result = await db.execute(
        select(Skill).where((Skill.skill_name == skill_name) | (Skill.skill_id == skill_name))
    )
    skill = result.scalar_one_or_none()
    if skill is None:
        raise NotFoundError(detail=f"Skill '{skill_name}' not found")
    return skill


async def _resolve_stage(db: AsyncSession, stage_id: str | None) -> ProjectStage:
    """Resolve project stage by ID.

    Args:
        db: Database session.
        stage_id: Project stage ID.

    Returns:
        ProjectStage ORM model.

    Raises:
        BadRequestError: stage_id is missing.
        NotFoundError: Stage not found.
    """
    if stage_id is None:
        raise BadRequestError(detail="target_stage_id is required")
    result = await db.execute(select(ProjectStage).where(ProjectStage.project_stage_id == stage_id))
    stage = result.scalar_one_or_none()
    if stage is None:
        raise NotFoundError(detail=f"Stage '{stage_id}' not found")
    return stage


@router.post(
    "/trigger",
    response_model=SkillExecutionResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def trigger_execution(
    dto: ExecutionTriggerDTO,
    db: AsyncSession = Depends(get_db),
) -> SkillExecution:
    """触发 Skill 执行。

    根据触发动作创建新的 SkillExecution 记录。
    """
    skill = await _resolve_skill(db, dto.target_skill_name)
    stage = await _resolve_stage(db, dto.target_stage_id)

    validator = TriggerValidator(SkillExecutionRepository(db))
    is_release = validator._is_release_skill(skill.skill_name)
    validation = await validator.validate_trigger(dto, skill.skill_name, is_release)

    if not validation.valid:
        if validation.error_code == "EXECUTION_ALREADY_IN_PROGRESS":
            raise ConflictError(detail=validation.message or "Execution in progress")
        if validation.error_code == "RETRY_LIMIT_EXCEEDED":
            raise ConflictError(detail=validation.message or "Retry limit exceeded")
        raise BadRequestError(detail=validation.message or "Validation failed")

    execution = SkillExecution(
        execution_id=str(uuid.uuid4()),
        project_id=stage.project_id,
        stage_id=dto.target_stage_id,
        skill_id=skill.skill_id,
        skill_name=skill.skill_name,
        trigger_action=dto.trigger_action,
        current_phase="NONE",
        phase_status="RUNNING",
        overall_status="NOT_STARTED",
        retry_count=0,
        previous_execution_id=dto.previous_execution_id,
        is_release_skill=is_release,
        release_confirmed=dto.confirm_release or False,
    )

    repo = SkillExecutionRepository(db)
    return await repo.create(execution)


@router.get("/{execution_id}/status", response_model=ExecutionStatusDTO)
async def get_execution_status(
    execution_id: str,
    last_anchor: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> ExecutionStatusDTO:
    """查询执行状态。"""
    aggregator = StatusAggregator(SkillExecutionRepository(db))
    return await aggregator.poll_execution_status(execution_id, last_anchor)


@router.get("/{execution_id}/logs", response_model=LogQueryResultDTO)
async def get_execution_logs(
    execution_id: str,
    keyword: str | None = None,
    level: str = "ALL",
    anchor: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> LogQueryResultDTO:
    """查询执行日志。"""
    filters = LogFilterDTO(keyword=keyword, level=level, anchor=anchor)
    service = LogCollectorService(ExecutionLogRepository(db))
    return await service.query_logs(execution_id, filters)


@router.post("/{execution_id}/retry", response_model=RetryResultDTO)
async def retry_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
) -> RetryResultDTO:
    """重试失败的执行。"""
    manager = RetryManager(SkillExecutionRepository(db))
    return await manager.attempt_retry(execution_id)


@router.post(
    "/{execution_id}/confirm-release",
    response_model=SkillExecutionResponseDTO,
)
async def confirm_release(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
) -> SkillExecution:
    """确认发布类 Skill 的执行。"""
    repo = SkillExecutionRepository(db)
    execution = await repo.get_by_id(execution_id)
    if execution is None:
        raise NotFoundError(detail=f"Execution '{execution_id}' not found")
    execution.release_confirmed = True
    return await repo.update(execution)


@router.get("", response_model=list[SkillExecutionResponseDTO])
async def list_executions(
    project_id: str | None = None,
    stage_id: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[SkillExecution]:
    """查询 SkillExecution 列表。

    支持按 project_id 或 stage_id 过滤；无过滤时返回最近 limit 条。
    """
    repo = SkillExecutionRepository(db)
    items: list[SkillExecution] = []
    if project_id:
        items = await repo.list_by_project(project_id)
    elif stage_id:
        items = await repo.list_by_stage(stage_id)
    else:
        stmt = select(SkillExecution).order_by(SkillExecution.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        items = list(result.scalars().all())
    return items


@router.post("/{execution_id}/stop", response_model=SkillExecutionResponseDTO)
async def stop_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
) -> SkillExecution:
    """停止执行中的 SkillExecution。"""
    repo = SkillExecutionRepository(db)
    execution = await repo.get_by_id(execution_id)
    if execution is None:
        raise NotFoundError(detail=f"Execution '{execution_id}' not found")
    if execution.overall_status not in ("RUNNING", "NOT_STARTED"):
        raise BadRequestError(detail="只能停止运行中或未开始的执行")
    execution.overall_status = "STOPPED"
    execution.phase_status = "STOPPED"
    return await repo.update(execution)


class _BatchTriggerPayload(BaseModel):
    """批量触发 Stage 下所有 Skill 的请求体。"""

    target_stage_id: str = Field(description="目标 Stage ID")
    project_id: str = Field(description="项目 ID")
    trigger_action: str = Field(default="BATCH_EXECUTE", description="触发动作")
    confirm_release: bool = Field(default=False, description="是否确认发布类 Skill")


@router.post(
    "/batch-trigger",
    response_model=list[SkillExecutionResponseDTO],
    status_code=status.HTTP_201_CREATED,
)
async def batch_trigger_execution(
    dto: _BatchTriggerPayload,
    db: AsyncSession = Depends(get_db),
) -> list[SkillExecution]:
    """批量触发 Stage 下所有关联 Skill 的执行。"""
    stage = await _resolve_stage(db, dto.target_stage_id)

    # 收集该 Stage 关联的所有 Skill ID
    skill_ids: set[str] = set()
    if stage.primary_skill_id:
        skill_ids.add(stage.primary_skill_id)

    exec_stmt = (
        select(SkillExecution.skill_id)
        .where(SkillExecution.stage_id == dto.target_stage_id)
        .distinct()
    )
    exec_result = await db.execute(exec_stmt)
    for row in exec_result.scalars().all():
        skill_ids.add(row)

    if not skill_ids:
        return []

    skill_stmt = select(Skill).where(Skill.skill_id.in_(skill_ids))
    skill_result = await db.execute(skill_stmt)
    skills = list(skill_result.scalars().all())

    validator = TriggerValidator(SkillExecutionRepository(db))
    repo = SkillExecutionRepository(db)
    executions: list[SkillExecution] = []

    for skill in skills:
        is_release = validator._is_release_skill(skill.skill_name)
        trigger_dto = ExecutionTriggerDTO(
            trigger_action=dto.trigger_action,
            target_stage_id=dto.target_stage_id,
            target_skill_name=skill.skill_id,
            confirm_release=dto.confirm_release if is_release else None,
        )
        validation = await validator.validate_trigger(trigger_dto, skill.skill_name, is_release)
        if not validation.valid:
            # 跳过无法触发的 Skill（如已在运行或未确认发布）
            continue

        execution = SkillExecution(
            execution_id=str(uuid.uuid4()),
            project_id=dto.project_id,
            stage_id=dto.target_stage_id,
            skill_id=skill.skill_id,
            skill_name=skill.skill_name,
            trigger_action=dto.trigger_action,
            current_phase="NONE",
            phase_status="RUNNING",
            overall_status="NOT_STARTED",
            retry_count=0,
            previous_execution_id=None,
            is_release_skill=is_release,
            release_confirmed=dto.confirm_release or False,
        )
        executions.append(await repo.create(execution))

    return executions
