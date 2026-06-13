"""Stage orchestrator service."""

from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.infrastructure.database.repositories.parallel_group_repo import (
    ParallelGroupRepository,
)
from app.infrastructure.database.repositories.plan_node_repo import PlanNodeRepository
from app.schemas.execution_plan import (
    StageCompletionDTO,
    StageExecutionResultDTO,
    StageReadinessDTO,
)


class StageOrchestrator:
    """Stage 编排器，负责 Stage 就绪检查与内部分组调度。"""

    def __init__(
        self,
        node_repo: PlanNodeRepository,
        group_repo: ParallelGroupRepository,
    ) -> None:
        """Initialize with repositories."""
        self._node_repo = node_repo
        self._group_repo = group_repo

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
        nodes = await self._node_repo.list_by_stage(plan_id, stage_id)
        if not nodes:
            raise NotFoundError(
                detail=f"No nodes found for stage '{stage_id}'"
            )

        node_results: list[dict[str, str]] = []

        # 主 Skill 先执行
        primary_nodes = [n for n in nodes if n.node_type == "primary"]
        for node in primary_nodes:
            node.status = "EXECUTING"
            await self._node_repo.update(node)
            node.status = "COMPLETED"
            await self._node_repo.update(node)
            node_results.append(
                {"node_id": node.node_id, "status": node.status}
            )

        # 辅助 Skill 并行执行（MVP 简化：依次更新）
        auxiliary_nodes = [n for n in nodes if n.node_type == "auxiliary"]
        for node in auxiliary_nodes:
            node.status = "EXECUTING"
            await self._node_repo.update(node)
            node.status = "COMPLETED"
            await self._node_repo.update(node)
            node_results.append(
                {"node_id": node.node_id, "status": node.status}
            )

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
