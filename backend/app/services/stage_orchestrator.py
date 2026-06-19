"""Stage orchestrator service."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.event_bus import DomainEvent, EventBus, get_event_bus
from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.infrastructure.database.repositories.parallel_group_repo import (
    ParallelGroupRepository,
)
from app.infrastructure.database.repositories.plan_node_repo import PlanNodeRepository
from app.models.artifact import ArtifactFile
from app.models.execution_log import ExecutionLog
from app.models.project import Project
from app.models.project_path_config import ProjectPathConfig
from app.models.project_stage import ProjectStage
from app.models.skill_execution import SkillExecution
from app.models.stage_rollback_log import StageRollbackLog
from app.models.stage_skill_binding import StageSkillBinding
from app.models.template_stage import TemplateStage
from app.schemas.execution_plan import (
    StageCompletionDTO,
    StageExecutionResultDTO,
    StageReadinessDTO,
)
from app.services.pocketflow.engine import PhaseResult, PocketFlowEngine
from app.services.pocketflow.lock_manager import LockManager
from app.services.skill_resolver import SkillResolver
from app.services.stage_gate_controller import StageGateController


class StageOrchestrator:
    """Stage 编排器。

    同时兼容两种使用方式：
    1. 基于 ExecutionPlan 的 PlanNode/ParallelGroup 调度（已有接口）。
    2. 基于 ProjectStage + StageSkillBinding 的项目级阶段状态机（重构新增）。

    真实 Skill 执行：
    - 默认使用 ``PocketFlowEngine`` + ``KimiCLIAdapter`` 调用本地 ``kimi`` CLI。
    - 测试可注入 ``MockCLIAdapter`` 或完整 ``PocketFlowEngine`` 实例。
    """

    def __init__(
        self,
        node_repo: PlanNodeRepository | None = None,
        group_repo: ParallelGroupRepository | None = None,
        session: AsyncSession | None = None,
        event_bus: EventBus | None = None,
        pocketflow_engine: PocketFlowEngine | None = None,
        skill_resolver: SkillResolver | None = None,
    ) -> None:
        """Initialize with repositories or an async session."""
        self._node_repo = node_repo
        self._group_repo = group_repo
        self._session = session
        self._event_bus = event_bus or get_event_bus()
        self._pocketflow_engine = pocketflow_engine
        self._skill_resolver = skill_resolver

    def _engine(self) -> PocketFlowEngine:
        """Return the configured PocketFlow engine or create a real one."""
        if self._pocketflow_engine is None:
            self._pocketflow_engine = PocketFlowEngine(lock_manager=LockManager())
        return self._pocketflow_engine

    def _resolver(self) -> SkillResolver:
        """Return the configured skill resolver or create a default one."""
        if self._skill_resolver is not None:
            return self._skill_resolver
        return SkillResolver(session=self._require_session())

    def _publish_stage_event(
        self,
        stage: ProjectStage,
        event_type: str,
        extra_payload: dict[str, Any],
    ) -> None:
        """Publish a stage/skill event to the event bus and SSE clients."""
        payload: dict[str, Any] = {
            "project_id": stage.project_id,
            "stage_id": stage.project_stage_id,
            "business_stage_key": stage.stage_id,
            **extra_payload,
        }
        self._event_bus.publish(
            DomainEvent(
                event_type=event_type,
                aggregate_id=stage.project_id,
                payload=payload,
            )
        )
        try:
            from app.api.v1.advanced import _get_notification_manager

            manager = _get_notification_manager()
            manager.broadcast(stage.project_id, event_type, payload)
        except Exception:
            # NotificationManager is optional; never fail the core workflow.
            pass

    # ============================================================
    # Legacy ExecutionPlan-based methods (kept for compatibility)
    # ============================================================
    async def check_stage_readiness(
        self,
        stage_id: str,
        plan_id: str,
        upstream_stages: list[str],
        gate_passed: bool,
    ) -> StageReadinessDTO:
        """检查 Stage 是否就绪。

        上游 stage 的所有节点必须 COMPLETED，且 Gate 必须通过。

        Args:
            stage_id: 当前 Stage ID。
            plan_id: 计划 ID。
            upstream_stages: 上游 Stage ID 列表。
            gate_passed: Gate 是否通过。

        Returns:
            Stage 就绪状态 DTO。
        """
        if self._node_repo is None:
            raise RuntimeError("PlanNodeRepository is required for this method")

        for upstream_stage in upstream_stages:
            nodes = await self._node_repo.list_by_stage(plan_id, upstream_stage)
            if any(n.status != "COMPLETED" for n in nodes):
                return StageReadinessDTO(
                    stage_id=stage_id,
                    ready=False,
                    reason="上游未完成",
                )

        if not gate_passed:
            return StageReadinessDTO(
                stage_id=stage_id,
                ready=False,
                reason="Gate 未通过",
            )

        return StageReadinessDTO(
            stage_id=stage_id,
            ready=True,
        )

    async def schedule_stage_execution(
        self,
        stage_id: str,
        plan_id: str,
    ) -> StageExecutionResultDTO:
        """调度 Stage 内 Skill 执行。

        MVP 简化：更新节点状态为 EXECUTING / COMPLETED。

        Args:
            stage_id: Stage ID。
            plan_id: 计划 ID。

        Returns:
            Stage 执行结果 DTO。
        """
        if self._node_repo is None:
            raise RuntimeError("PlanNodeRepository is required for this method")

        nodes = await self._node_repo.list_by_stage(plan_id, stage_id)
        if not nodes:
            raise NotFoundError(detail=f"No nodes found for stage '{stage_id}'")

        node_results: list[dict[str, str]] = []

        # 主 Skill 先执行
        primary_nodes = [n for n in nodes if n.node_type == "primary"]
        for node in primary_nodes:
            node.status = "EXECUTING"
            await self._node_repo.update(node)
            node.status = "COMPLETED"
            await self._node_repo.update(node)
            node_results.append({"node_id": node.node_id, "status": node.status})

        # 辅助 Skill 并行执行（MVP 简化：依次更新）
        auxiliary_nodes = [n for n in nodes if n.node_type == "auxiliary"]
        for node in auxiliary_nodes:
            node.status = "EXECUTING"
            await self._node_repo.update(node)
            node.status = "COMPLETED"
            await self._node_repo.update(node)
            node_results.append({"node_id": node.node_id, "status": node.status})

        return StageExecutionResultDTO(
            stage_id=stage_id,
            status="COMPLETED",
            node_results=node_results,
        )

    async def evaluate_stage_completion(
        self,
        stage_id: str,
        plan_id: str,
    ) -> StageCompletionDTO:
        """判定 Stage 完成状态。

        Args:
            stage_id: Stage ID。
            plan_id: 计划 ID。

        Returns:
            Stage 完成判定 DTO。
        """
        if self._node_repo is None:
            raise RuntimeError("PlanNodeRepository is required for this method")

        nodes = await self._node_repo.list_by_stage(plan_id, stage_id)
        primary_nodes = [n for n in nodes if n.node_type == "primary"]
        auxiliary_nodes = [n for n in nodes if n.node_type == "auxiliary"]

        if any(n.status == "FAILED" for n in primary_nodes):
            return StageCompletionDTO(
                stage_id=stage_id,
                completion_status="FAILED",
                warning_count=0,
            )

        primary_ok = all(n.status == "COMPLETED" for n in primary_nodes)
        auxiliary_ok = all(n.status == "COMPLETED" for n in auxiliary_nodes)
        auxiliary_failed = [n for n in auxiliary_nodes if n.status == "FAILED"]

        if primary_ok and auxiliary_ok:
            return StageCompletionDTO(
                stage_id=stage_id,
                completion_status="COMPLETED",
                warning_count=0,
            )

        if primary_ok and auxiliary_failed:
            return StageCompletionDTO(
                stage_id=stage_id,
                completion_status="COMPLETED_WITH_WARNING",
                warning_count=len(auxiliary_failed),
            )

        return StageCompletionDTO(
            stage_id=stage_id,
            completion_status="FAILED",
            warning_count=0,
        )

    # ============================================================
    # ProjectStage runtime state machine methods (Batch 2)
    # ============================================================
    async def start_project(self, project_id: str, operator_id: str = "system") -> dict[str, Any]:
        """启动项目阶段流水线。

        将首个未跳过的阶段置为 READY；若执行策略为 full_auto，则自动启动首个阶段。
        """
        session = self._require_session()
        proj = await session.get(Project, project_id)
        if proj is None:
            raise NotFoundError(detail=f"Project '{project_id}' not found")

        stages = await self._list_project_stages(project_id)
        if not stages:
            raise NotFoundError(detail=f"No stages found for project '{project_id}'")

        first_stage = stages[0]
        if first_stage.runtime_status not in ("not_started", "ready", "blocked"):
            raise ConflictError(
                detail=f"Project already started (stage status={first_stage.runtime_status})"
            )

        first_stage.runtime_status = "ready"
        session.add(first_stage)
        await session.flush()

        proj.current_stage_id = first_stage.project_stage_id
        session.add(proj)
        await session.flush()

        if proj.execution_strategy == "full_auto":
            return await self.execute_stage(first_stage.project_stage_id, operator_id)

        await session.commit()
        return {
            "project_id": project_id,
            "current_stage_id": first_stage.project_stage_id,
            "status": first_stage.runtime_status,
        }

    async def execute_stage(
        self,
        project_stage_id: str,
        operator_id: str = "system",
    ) -> dict[str, Any]:
        """触发阶段执行：启动、真实执行 Skill、完成/失败判定。"""
        start_result = await self.start_stage(project_stage_id, operator_id)

        execution_summary = await self._execute_skill_bindings(
            project_stage_id,
            start_result["execution_ids"],
        )

        if execution_summary["primary_failed"]:
            return await self._fail_stage(project_stage_id, execution_summary["error"])

        return await self.complete_stage(project_stage_id)

    async def start_stage(
        self,
        project_stage_id: str,
        operator_id: str = "system",
    ) -> dict[str, Any]:
        """启动阶段：状态机校验、创建 SkillExecution 记录。"""
        session = self._require_session()
        stage = await session.get(ProjectStage, project_stage_id)
        if stage is None:
            raise NotFoundError(detail=f"Stage '{project_stage_id}' not found")

        allowed = {"not_started", "ready", "blocked"}
        if stage.runtime_status not in allowed:
            raise ConflictError(
                detail=f"Cannot start stage from status '{stage.runtime_status}'"
            )

        old_status = stage.runtime_status
        stage.runtime_status = "in_progress"
        stage.execution_status = "IN_PROGRESS"
        stage.started_at = datetime.now(UTC)
        session.add(stage)
        await session.flush()

        proj = await session.get(Project, stage.project_id)
        if proj is not None:
            proj.current_stage_id = stage.project_stage_id
            session.add(proj)
            await session.flush()

        bindings = await self._list_bindings(project_stage_id)
        execution_ids: list[str] = []
        for binding in bindings:
            execution = SkillExecution(
                execution_id=str(uuid.uuid4()),
                project_id=stage.project_id,
                stage_id=project_stage_id,
                skill_id=binding.skill_id,
                skill_name=binding.skill_id,
                trigger_action="BATCH_EXECUTE",
                current_phase="EXEC",
                phase_status="RUNNING",
                overall_status="RUNNING",
                started_at=datetime.now(UTC),
            )
            session.add(execution)
            await session.flush()
            execution_ids.append(execution.execution_id)
            self._publish_stage_event(
                stage,
                "skill.execution_updated",
                {
                    "execution_id": execution.execution_id,
                    "skill_id": execution.skill_id,
                    "status": execution.overall_status,
                },
            )

        self._publish_stage_event(
            stage,
            "stage.status_changed",
            {"old_status": old_status, "new_status": stage.runtime_status},
        )
        await session.commit()
        return {
            "project_stage_id": project_stage_id,
            "execution_ids": execution_ids,
            "status": stage.runtime_status,
        }

    async def _execute_skill_bindings(
        self,
        project_stage_id: str,
        execution_ids: list[str],
    ) -> dict[str, Any]:
        """真实执行阶段绑定的所有 Skill。

        主 Skill 先串行执行，全部成功后再并行执行辅助 Skill。执行结果会回写
        ``SkillExecution`` 记录，成功时写入产物 ``ArtifactFile`` 记录。

        Returns:
            Summary dict with ``primary_failed``, ``any_failed``, ``error``,
            ``executed_skill_ids`` and ``artifact_ids``.
        """
        session = self._require_session()
        stage = await session.get(ProjectStage, project_stage_id)
        if stage is None:
            raise NotFoundError(detail=f"Stage '{project_stage_id}' not found")

        bindings = await self._list_bindings(project_stage_id)
        executions = [
            await session.get(SkillExecution, execution_id)
            for execution_id in execution_ids
        ]
        execution_map = {execution.skill_id: execution for execution in executions if execution}

        primary_bindings = [b for b in bindings if b.role == "primary"]
        auxiliary_bindings = [b for b in bindings if b.role == "auxiliary"]

        summary: dict[str, Any] = {
            "primary_failed": False,
            "any_failed": False,
            "error": None,
            "executed_skill_ids": [],
            "artifact_ids": [],
        }

        project_dir = settings.project_root / "projects" / stage.project_id
        work_dir = str(project_dir / "artifacts")
        Path(work_dir).mkdir(parents=True, exist_ok=True)

        engine = self._engine()
        resolver = self._resolver()

        async def _run_binding(binding: StageSkillBinding) -> bool:
            execution = execution_map.get(binding.skill_id)
            if execution is None:
                execution = SkillExecution(
                    execution_id=str(uuid.uuid4()),
                    project_id=stage.project_id,
                    stage_id=project_stage_id,
                    skill_id=binding.skill_id,
                    skill_name=binding.skill_id,
                    trigger_action="BATCH_EXECUTE",
                    current_phase="EXEC",
                    phase_status="RUNNING",
                    overall_status="RUNNING",
                    started_at=datetime.now(UTC),
                )
                session.add(execution)
                await session.flush()

            try:
                skill_path = await resolver.resolve(binding.skill_id)
            except FileNotFoundError as exc:
                execution.overall_status = "FAILED"
                execution.phase_status = "FAILED"
                execution.current_phase = "EXEC"
                execution.completed_at = datetime.now(UTC)
                session.add(execution)
                self._publish_stage_event(
                    stage,
                    "skill.execution_updated",
                    {
                        "execution_id": execution.execution_id,
                        "skill_id": execution.skill_id,
                        "status": execution.overall_status,
                        "error": str(exc),
                    },
                )
                summary["error"] = summary["error"] or str(exc)
                return False

            result = await engine.execute(
                skill_path=skill_path,
                project_id=stage.project_id,
                work_dir=work_dir,
                expected_artifacts=[],
            )

            success = result.final_status == "PASSED"
            execution.overall_status = "SUCCESS" if success else "FAILED"
            execution.phase_status = "COMPLETED" if success else "FAILED"
            execution.current_phase = "POST"
            execution.completed_at = datetime.now(UTC)
            session.add(execution)
            await session.flush()

            self._publish_stage_event(
                stage,
                "skill.execution_updated",
                {
                    "execution_id": execution.execution_id,
                    "skill_id": execution.skill_id,
                    "status": execution.overall_status,
                    "stdout": result.stdout[:500],
                    "stderr": result.stderr[:500],
                },
            )

            if success:
                post_phase = result.phase_results.get("post")
                if isinstance(post_phase, PhaseResult):
                    for artifact_rel in post_phase.output_artifacts or []:
                        artifact_id = str(uuid.uuid4())
                        full_path = (Path(work_dir) / artifact_rel).resolve()
                        artifact = ArtifactFile(
                            artifact_id=artifact_id,
                            project_id=stage.project_id,
                            stage_id=project_stage_id,
                            execution_id=execution.execution_id,
                            file_name=Path(artifact_rel).name,
                            file_path=str(full_path),
                            file_type=self._map_artifact_file_type(artifact_rel),
                            file_size_bytes=full_path.stat().st_size if full_path.exists() else 0,
                        )
                        session.add(artifact)
                        await session.flush()
                        summary["artifact_ids"].append(artifact_id)
                if result.stdout:
                    self._append_execution_log(
                        session, execution.execution_id, "INFO", result.stdout[:2000]
                    )
            else:
                exec_phase = result.phase_results.get("exec")
                prep_phase = result.phase_results.get("prep")
                error_msg = (
                    (isinstance(exec_phase, PhaseResult) and exec_phase.error_msg)
                    or (isinstance(prep_phase, PhaseResult) and prep_phase.error_msg)
                    or "Skill execution failed"
                )
                summary["error"] = summary["error"] or error_msg
                self._append_execution_log(
                    session, execution.execution_id, "ERROR", error_msg
                )
                if result.stderr:
                    self._append_execution_log(
                        session, execution.execution_id, "ERROR", result.stderr[:2000]
                    )

            return success

        # 主 Skill 串行
        for binding in primary_bindings:
            summary["executed_skill_ids"].append(binding.skill_id)
            if not await _run_binding(binding):
                summary["primary_failed"] = True
                summary["any_failed"] = True

        if not summary["primary_failed"] and auxiliary_bindings:
            # 辅助 Skill 并行
            results = await asyncio.gather(
                *[_run_binding(b) for b in auxiliary_bindings],
                return_exceptions=True,
            )
            for idx, binding in enumerate(auxiliary_bindings):
                res = results[idx]
                summary["executed_skill_ids"].append(binding.skill_id)
                if isinstance(res, Exception) or res is False:
                    summary["any_failed"] = True
                    if summary["error"] is None and isinstance(res, Exception):
                        summary["error"] = str(res)

        await session.commit()
        return summary

    async def _fail_stage(
        self,
        project_stage_id: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """将阶段标记为失败/阻塞。"""
        session = self._require_session()
        stage = await session.get(ProjectStage, project_stage_id)
        if stage is None:
            raise NotFoundError(detail=f"Stage '{project_stage_id}' not found")

        old_status = stage.runtime_status
        stage.runtime_status = "blocked"
        stage.execution_status = "BLOCKED"
        session.add(stage)
        await session.flush()

        self._publish_stage_event(
            stage,
            "stage.status_changed",
            {"old_status": old_status, "new_status": stage.runtime_status},
        )
        await session.commit()
        return {
            "project_stage_id": project_stage_id,
            "status": stage.runtime_status,
            "error": reason,
        }

    async def complete_stage(
        self,
        project_stage_id: str,
    ) -> dict[str, Any]:
        """阶段完成回调：根据执行策略决定 REVIEW_PENDING / GATE_PENDING / PASSED。"""
        session = self._require_session()
        stage = await session.get(ProjectStage, project_stage_id)
        if stage is None:
            raise NotFoundError(detail=f"Stage '{project_stage_id}' not found")
        if stage.runtime_status != "in_progress":
            raise ConflictError(
                detail=f"Cannot complete stage from status '{stage.runtime_status}'"
            )

        # SkillExecution records are updated by _execute_skill_bindings.
        stage.execution_status = "COMPLETED"
        session.add(stage)
        await session.flush()

        proj = await session.get(Project, stage.project_id)
        strategy = stage.execution_strategy or proj.execution_strategy if proj else "semi_auto"

        if strategy == "full_auto":
            old_status = stage.runtime_status
            stage.runtime_status = "passed"
            stage.completed_at = datetime.now(UTC)
            session.add(stage)
            await session.flush()
            self._publish_stage_event(
                stage,
                "stage.status_changed",
                {"old_status": old_status, "new_status": stage.runtime_status},
            )
            advanced = await self._advance_and_maybe_start(stage)
            return {
                "project_stage_id": project_stage_id,
                "status": stage.runtime_status,
                "next_stage_id": advanced["next_stage_id"] if advanced else None,
                "auto_started": advanced["auto_started"] if advanced else False,
            }

        if strategy == "semi_auto":
            # 需求/设计阶段需要 Gate，其他直接 PASSED
            old_status = stage.runtime_status
            gate_required = stage.is_gate_required
            if gate_required:
                stage.runtime_status = "review_pending"
            else:
                stage.runtime_status = "passed"
                stage.completed_at = datetime.now(UTC)
            session.add(stage)
            await session.flush()
            self._publish_stage_event(
                stage,
                "stage.status_changed",
                {"old_status": old_status, "new_status": stage.runtime_status},
            )

            if gate_required:
                await self._gate_controller().create_gate(
                    stage.project_stage_id,
                    stage.project_id,
                    gate_type="2",
                    reason="阶段完成，等待人工确认",
                )
                self._publish_stage_event(
                    stage,
                    "stage.gate_pending",
                    {
                        "gate_type": "2",
                        "summary": "阶段完成，等待人工确认",
                    },
                )

            if stage.runtime_status == "passed":
                advanced = await self._advance_and_maybe_start(stage)
                return {
                    "project_stage_id": project_stage_id,
                    "status": stage.runtime_status,
                    "next_stage_id": advanced["next_stage_id"] if advanced else None,
                    "auto_started": advanced["auto_started"] if advanced else False,
                }

            await session.commit()
            return {
                "project_stage_id": project_stage_id,
                "status": stage.runtime_status,
                "next_stage_id": None,
                "auto_started": False,
            }

        # full_manual
        old_status = stage.runtime_status
        stage.runtime_status = "gate_pending"
        session.add(stage)
        await session.flush()
        self._publish_stage_event(
            stage,
            "stage.status_changed",
            {"old_status": old_status, "new_status": stage.runtime_status},
        )
        await self._gate_controller().create_gate(
            stage.project_stage_id,
            stage.project_id,
            gate_type="2",
            reason="全人工模式，需人工确认",
        )
        self._publish_stage_event(
            stage,
            "stage.gate_pending",
            {
                "gate_type": "2",
                "summary": "全人工模式，需人工确认",
            },
        )
        await session.commit()
        return {
            "project_stage_id": project_stage_id,
            "status": stage.runtime_status,
            "next_stage_id": None,
            "auto_started": False,
        }

    async def advance_stage(
        self,
        project_stage_id: str,
        operator_id: str = "system",
    ) -> dict[str, Any]:
        """手动推进到下一阶段（适用于半自动/全人工模式 Gate 通过后）。"""
        session = self._require_session()
        stage = await session.get(ProjectStage, project_stage_id)
        if stage is None:
            raise NotFoundError(detail=f"Stage '{project_stage_id}' not found")
        if stage.runtime_status not in ("review_pending", "gate_pending", "passed"):
            raise ConflictError(
                detail=f"Cannot advance stage from status '{stage.runtime_status}'"
            )

        if stage.runtime_status in ("review_pending", "gate_pending"):
            await self._gate_controller().decide(
                project_stage_id, "pass", operator_id, "手动推进"
            )
            old_status = stage.runtime_status
            stage.runtime_status = "passed"
            stage.completed_at = datetime.now(UTC)
            session.add(stage)
            await session.flush()
            self._publish_stage_event(
                stage,
                "stage.status_changed",
                {"old_status": old_status, "new_status": stage.runtime_status},
            )

        advanced = await self._advance_and_maybe_start(stage)
        await session.commit()
        return {
            "project_stage_id": project_stage_id,
            "status": stage.runtime_status,
            "next_stage_id": advanced["next_stage_id"] if advanced else None,
            "auto_started": advanced["auto_started"] if advanced else False,
        }

    async def decide_gate(
        self,
        project_stage_id: str,
        decision: str,
        reason: str | None = None,
        operator_id: str = "system",
    ) -> dict[str, Any]:
        """Gate 决策：pass 则推进，reject 则阻塞。"""
        session = self._require_session()
        stage = await session.get(ProjectStage, project_stage_id)
        if stage is None:
            raise NotFoundError(detail=f"Stage '{project_stage_id}' not found")
        if stage.runtime_status not in ("review_pending", "gate_pending"):
            raise ConflictError(
                detail=f"Cannot decide gate from status '{stage.runtime_status}'"
            )

        decision = decision.lower()
        await self._gate_controller().decide(
            project_stage_id, decision, operator_id, reason
        )
        if decision == "pass":
            old_status = stage.runtime_status
            stage.runtime_status = "passed"
            stage.completed_at = datetime.now(UTC)
            session.add(stage)
            await session.flush()
            self._publish_stage_event(
                stage,
                "stage.status_changed",
                {"old_status": old_status, "new_status": stage.runtime_status},
            )
            advanced = await self._advance_and_maybe_start(stage)
            await session.commit()
            return {
                "project_stage_id": project_stage_id,
                "status": stage.runtime_status,
                "next_stage_id": advanced["next_stage_id"] if advanced else None,
                "auto_started": advanced["auto_started"] if advanced else False,
            }
        if decision == "reject":
            old_status = stage.runtime_status
            stage.runtime_status = "blocked"
            session.add(stage)
            await session.flush()
            self._publish_stage_event(
                stage,
                "stage.status_changed",
                {"old_status": old_status, "new_status": stage.runtime_status},
            )
            await session.commit()
            return {
                "project_stage_id": project_stage_id,
                "status": stage.runtime_status,
                "reason": reason,
            }
        raise ValidationError(detail="decision must be 'pass' or 'reject'")

    async def rollback_stage(
        self,
        project_stage_id: str,
        target_stage_id: str,
        reason: str | None = None,
        operator_id: str = "system",
    ) -> dict[str, Any]:
        """回滚到目标阶段，重置下游阶段并标记产物过期。

        Args:
            project_stage_id: 当前阶段 ID。
            target_stage_id: 回滚目标阶段 ID。
            reason: 回滚原因。
            operator_id: 操作者 ID。

        Returns:
            回滚结果摘要。
        """
        session = self._require_session()
        current = await session.get(ProjectStage, project_stage_id)
        if current is None:
            raise NotFoundError(detail=f"Stage '{project_stage_id}' not found")
        target = await session.get(ProjectStage, target_stage_id)
        if target is None:
            raise NotFoundError(detail=f"Target stage '{target_stage_id}' not found")
        if current.project_id != target.project_id:
            raise ValidationError(detail="Current and target stages belong to different projects")
        if target.order_index > current.order_index:
            raise ValidationError(detail="Target stage must be before or equal to current stage")
        if target.project_stage_id == current.project_stage_id:
            raise ValidationError(detail="Target stage cannot be the current stage")

        project_id = current.project_id
        stages = await self._list_project_stages(project_id)

        reset_stage_ids: list[str] = []
        for stage in stages:
            if stage.order_index > target.order_index:
                old_status = stage.runtime_status
                stage.runtime_status = "not_started"
                stage.started_at = None
                stage.completed_at = None
                session.add(stage)
                reset_stage_ids.append(stage.project_stage_id)
                self._publish_stage_event(
                    stage,
                    "stage.status_changed",
                    {"old_status": old_status, "new_status": stage.runtime_status},
                )

        target_old_status = target.runtime_status
        target.runtime_status = "ready"
        session.add(target)
        self._publish_stage_event(
            target,
            "stage.status_changed",
            {"old_status": target_old_status, "new_status": target.runtime_status},
        )

        stale_artifact_ids: list[str] = []
        if reset_stage_ids:
            artifact_stmt = select(ArtifactFile).where(
                ArtifactFile.project_id == project_id,
                ArtifactFile.stage_id.in_(reset_stage_ids),
            )
            artifact_result = await session.execute(artifact_stmt)
            for artifact in artifact_result.scalars().all():
                artifact.stale_flag = True
                session.add(artifact)
                stale_artifact_ids.append(artifact.artifact_id)

        rollback_log = StageRollbackLog(
            log_id=str(uuid.uuid4()),
            project_id=project_id,
            from_stage_id=current.project_stage_id,
            to_stage_id=target.project_stage_id,
            reason=reason,
            stale_artifact_ids=json.dumps(stale_artifact_ids),
            operator_id=operator_id,
        )
        session.add(rollback_log)
        await session.flush()

        self._publish_stage_event(
            target,
            "stage.rollback_complete",
            {
                "project_id": project_id,
                "target_stage_id": target.project_stage_id,
                "reset_stage_ids": reset_stage_ids,
            },
        )

        await session.commit()
        return {
            "project_id": project_id,
            "target_stage_id": target.project_stage_id,
            "reset_stage_ids": reset_stage_ids,
            "stale_artifact_ids": stale_artifact_ids,
        }

    async def get_stage_progress(self, project_id: str) -> dict[str, Any]:
        """获取项目阶段进度与状态聚合。"""
        session = self._require_session()
        proj = await session.get(Project, project_id)
        if proj is None:
            raise NotFoundError(detail=f"Project '{project_id}' not found")

        stages = await self._list_project_stages(project_id)
        total = len(stages)
        passed = sum(1 for s in stages if s.runtime_status == "passed")
        current_stage_id = proj.current_stage_id

        merge_policy = await self._load_merge_policy(project_id)
        group_map = self._build_merge_group_map(merge_policy)
        business_key_map = await self._load_business_stage_keys(project_id)

        stage_items = []
        for s in stages:
            progress = self._runtime_progress(s.runtime_status)
            business_stage_key = business_key_map.get(s.project_stage_id, s.stage_id)
            group = group_map.get(business_stage_key)
            stage_items.append(
                {
                    "project_stage_id": s.project_stage_id,
                    "stage_id": s.stage_id,
                    "order_index": s.order_index,
                    "business_stage_key": business_stage_key,
                    "merge_group_label": group["label"] if group else None,
                    "merged_stage_keys": group["keys"] if group else None,
                    "runtime_status": s.runtime_status,
                    "primary_skill_id": s.primary_skill_id,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                    "progress_percent": progress,
                }
            )

        progress_percent = round(passed / total * 100) if total else 0
        return {
            "project_id": project_id,
            "execution_strategy": proj.execution_strategy,
            "current_stage_id": current_stage_id,
            "progress_percent": progress_percent,
            "stages": stage_items,
        }

    # ============================================================
    # Helpers
    # ============================================================
    @staticmethod
    def _map_artifact_file_type(artifact_path: str) -> str:
        """Map a file suffix to the ArtifactFile.file_type enum."""
        suffix = Path(artifact_path).suffix.lower()
        mapping = {
            ".md": "md",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".txt": "txt",
        }
        return mapping.get(suffix, "other")

    @staticmethod
    def _append_execution_log(
        session: AsyncSession,
        execution_id: str,
        level: str,
        content: str,
    ) -> None:
        """Append a persisted execution log entry without committing."""
        log = ExecutionLog(
            log_id=str(uuid.uuid4()),
            execution_id=execution_id,
            log_anchor=str(uuid.uuid4())[:16],
            level=level,
            content=content,
        )
        session.add(log)

    def _require_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("AsyncSession is required for this method")
        return self._session

    def _gate_controller(self) -> StageGateController:
        return StageGateController(self._require_session())

    async def _load_merge_policy(self, project_id: str) -> dict[str, Any] | None:
        """Load merge policy JSON for a project."""
        session = self._require_session()
        path_config_result = await session.execute(
            select(ProjectPathConfig).where(ProjectPathConfig.project_id == project_id)
        )
        path_config = path_config_result.scalar_one_or_none()
        raw_policy = path_config.merge_policy_json if path_config else None
        if not raw_policy:
            proj = await session.get(Project, project_id)
            raw_policy = proj.merge_policy_json if proj else None
        if not raw_policy:
            return None
        try:
            policy = json.loads(raw_policy)
        except json.JSONDecodeError:
            return None
        if isinstance(policy, dict):
            return policy
        return None

    @staticmethod
    def _build_merge_group_map(
        merge_policy: dict[str, Any] | None,
    ) -> dict[str, dict[str, Any]]:
        """Map business stage keys to their merge group metadata."""
        if not merge_policy:
            return {}
        result: dict[str, dict[str, Any]] = {}
        for group in merge_policy.get("groups", []):
            keys = group.get("business_stage_keys", [])
            label = group.get("label")
            for key in keys:
                result[key] = {"label": label, "keys": keys}
        return result

    async def _load_business_stage_keys(self, project_id: str) -> dict[str, str]:
        """Map project_stage_id to business_stage_key via TemplateStage."""
        session = self._require_session()
        stmt = (
            select(ProjectStage.project_stage_id, TemplateStage.business_stage_key)
            .join(
                TemplateStage,
                ProjectStage.stage_id == TemplateStage.business_stage_key,
                isouter=True,
            )
            .where(ProjectStage.project_id == project_id)
        )
        result = await session.execute(stmt)
        return {
            row.project_stage_id: (row.business_stage_key or row.project_stage_id)
            for row in result.all()
        }

    async def _list_project_stages(self, project_id: str) -> list[ProjectStage]:
        session = self._require_session()
        stmt = (
            select(ProjectStage)
            .where(ProjectStage.project_id == project_id)
            .order_by(ProjectStage.order_index.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _list_bindings(self, project_stage_id: str) -> list[StageSkillBinding]:
        session = self._require_session()
        stmt = (
            select(StageSkillBinding)
            .where(StageSkillBinding.project_stage_id == project_stage_id)
            .order_by(StageSkillBinding.execution_order.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _find_next_stage(self, current: ProjectStage) -> ProjectStage | None:
        session = self._require_session()
        stmt = (
            select(ProjectStage)
            .where(
                ProjectStage.project_id == current.project_id,
                ProjectStage.order_index > current.order_index,
                ProjectStage.runtime_status != "skipped",
            )
            .order_by(ProjectStage.order_index.asc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _advance_and_maybe_start(
        self,
        current: ProjectStage,
        operator_id: str = "system",
    ) -> dict[str, Any] | None:
        session = self._require_session()
        next_stage = await self._find_next_stage(current)
        if next_stage is None:
            return None

        old_status = next_stage.runtime_status
        next_stage.runtime_status = "ready"
        session.add(next_stage)
        await session.flush()
        self._publish_stage_event(
            next_stage,
            "stage.status_changed",
            {"old_status": old_status, "new_status": next_stage.runtime_status},
        )

        proj = await session.get(Project, current.project_id)
        auto_start = proj is not None and proj.execution_strategy == "full_auto"
        if auto_start:
            self._publish_stage_event(
                current,
                "stage.auto_advance",
                {
                    "from_stage_id": current.project_stage_id,
                    "to_stage_id": next_stage.project_stage_id,
                },
            )
            await session.commit()
            started = await self.execute_stage(next_stage.project_stage_id, operator_id)
            return {
                "next_stage_id": next_stage.project_stage_id,
                "auto_started": True,
                "status": started["status"],
            }

        await session.commit()
        return {
            "next_stage_id": next_stage.project_stage_id,
            "auto_started": False,
            "status": next_stage.runtime_status,
        }

    @staticmethod
    def _runtime_progress(runtime_status: str) -> int:
        mapping = {
            "not_started": 0,
            "ready": 0,
            "in_progress": 50,
            "review_pending": 80,
            "gate_pending": 90,
            "passed": 100,
            "blocked": 30,
            "skipped": 100,
        }
        return mapping.get(runtime_status, 0)
