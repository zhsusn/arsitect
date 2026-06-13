"""Execution plan generator service."""

from __future__ import annotations

import json
import uuid
from collections import deque
from typing import Any

from app.core.exceptions import ValidationError
from app.infrastructure.database.repositories.execution_plan_repo import (
    ExecutionPlanRepository,
)
from app.infrastructure.database.repositories.parallel_group_repo import (
    ParallelGroupRepository,
)
from app.infrastructure.database.repositories.plan_node_repo import PlanNodeRepository
from app.models.execution_plan import ExecutionPlan
from app.models.parallel_group import ParallelGroup
from app.models.plan_node import PlanNode


class ExecutionPlanGenerator:
    """执行计划生成器，负责从 DAG + 模板生成可执行计划。"""

    def __init__(
        self,
        plan_repo: ExecutionPlanRepository,
        node_repo: PlanNodeRepository,
        group_repo: ParallelGroupRepository,
    ) -> None:
        """Initialize with repositories."""
        self._plan_repo = plan_repo
        self._node_repo = node_repo
        self._group_repo = group_repo

    async def generate_plan(
        self,
        project_id: str,
        template_level: str,
        skill_nodes: list[dict[str, Any]],
    ) -> ExecutionPlan:
        """生成执行计划。

        Kahn 拓扑排序确定节点顺序，按 stage 分组识别并行组。

        Args:
            project_id: 项目 ID。
            template_level: 模板级别。
            skill_nodes: DAG 节点列表，每个 dict 含 skill_id, stage_id,
                node_type, dependencies, module_id。

        Returns:
            创建好的 ExecutionPlan。

        Raises:
            ValidationError: 检测到环或 stage 主 Skill 数量不合法。
        """
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            project_id=project_id,
            version="v1.0",
            is_frozen=False,
            template_level=template_level,
        )
        await self._plan_repo.create(plan)

        # 拓扑排序
        sorted_nodes = self._topological_sort(skill_nodes)

        # 创建 PlanNode
        node_map: dict[str, PlanNode] = {}
        plan_nodes: list[PlanNode] = []
        for idx, node_data in enumerate(sorted_nodes):
            node_id = str(uuid.uuid4())
            node = PlanNode(
                node_id=node_id,
                plan_id=plan.plan_id,
                skill_id=node_data["skill_id"],
                stage_id=node_data["stage_id"],
                order_index=idx,
                node_type=node_data.get("node_type", "primary"),
                module_id=node_data.get("module_id"),
                status="NOT_STARTED",
            )
            plan_nodes.append(node)
            node_map[node_data["skill_id"]] = node

        if plan_nodes:
            await self._node_repo.create_batch(plan_nodes)

        # 按 stage 分组并创建 ParallelGroup
        stage_nodes: dict[str, list[PlanNode]] = {}
        for node in plan_nodes:
            stage_nodes.setdefault(node.stage_id, []).append(node)

        groups: list[ParallelGroup] = []
        for stage_id, nodes in stage_nodes.items():
            primary_nodes = [n for n in nodes if n.node_type == "primary"]
            if len(primary_nodes) != 1:
                raise ValidationError(
                    detail="PLAN_MULTIPLE_PRIMARY",
                )
            auxiliary_nodes = [n for n in nodes if n.node_type == "auxiliary"]

            groups.append(
                ParallelGroup(
                    group_id=str(uuid.uuid4()),
                    plan_id=plan.plan_id,
                    stage_id=stage_id,
                    group_type="primary_serial",
                    node_ids=json.dumps([primary_nodes[0].node_id]),
                )
            )
            if auxiliary_nodes:
                groups.append(
                    ParallelGroup(
                        group_id=str(uuid.uuid4()),
                        plan_id=plan.plan_id,
                        stage_id=stage_id,
                        group_type="auxiliary_parallel",
                        node_ids=json.dumps([n.node_id for n in auxiliary_nodes]),
                    )
                )

        if groups:
            await self._group_repo.create_batch(groups)

        return plan

    def _topological_sort(
        self, skill_nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Kahn 拓扑排序。

        Args:
            skill_nodes: DAG 节点列表。

        Returns:
            排序后的节点列表。

        Raises:
            ValidationError: 存在环时抛出 PLAN_CYCLE_DETECTED。
        """
        skill_map = {n["skill_id"]: n for n in skill_nodes}
        in_degree: dict[str, int] = {
            n["skill_id"]: len(n.get("dependencies", [])) for n in skill_nodes
        }
        adj: dict[str, list[str]] = {n["skill_id"]: [] for n in skill_nodes}

        for node in skill_nodes:
            for dep in node.get("dependencies", []):
                if dep in adj:
                    adj[dep].append(node["skill_id"])

        queue: deque[str] = deque(
            [sid for sid, deg in in_degree.items() if deg == 0]
        )
        result: list[dict[str, Any]] = []

        while queue:
            current = queue.popleft()
            result.append(skill_map[current])
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(skill_nodes):
            raise ValidationError(detail="PLAN_CYCLE_DETECTED")

        return result
