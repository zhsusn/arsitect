"""Execution plan generator service."""

from __future__ import annotations

import json
import uuid
from collections import deque
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.models.project_stage import ProjectStage
from app.models.stage_skill_binding import StageSkillBinding


class ExecutionPlanGenerator:
    """执行计划生成器，负责从 DAG + 模板生成可执行计划。"""

    def __init__(
        self,
        plan_repo: ExecutionPlanRepository,
        node_repo: PlanNodeRepository,
        group_repo: ParallelGroupRepository,
        session: AsyncSession | None = None,
    ) -> None:
        """Initialize with repositories and an optional session.

        Args:
            plan_repo: Execution plan repository.
            node_repo: Plan node repository.
            group_repo: Parallel group repository.
            session: Optional async session for ad-hoc queries.
        """
        self._plan_repo = plan_repo
        self._node_repo = node_repo
        self._group_repo = group_repo
        self._session = session or plan_repo._session

    async def generate_plan(
        self,
        project_id: str,
        template_level: str,
        skill_nodes: list[dict[str, Any]],
        execution_strategy: str | None = None,
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
            execution_strategy=execution_strategy or "semi_auto",
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

        # 构建依赖矩阵：node_id -> 依赖的 node_id 列表
        dependency_matrix: dict[str, list[str]] = {}
        for node_data in sorted_nodes:
            node = node_map[node_data["skill_id"]]
            dependency_matrix[node.node_id] = [
                node_map[dep].node_id
                for dep in node_data.get("dependencies", [])
                if dep in node_map
            ]
        plan.dependency_matrix = json.dumps(dependency_matrix)
        await self._plan_repo.update(plan)

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

    async def generate_plan_from_project(
        self,
        project_id: str,
        template_level: str | None,
        execution_strategy: str | None = None,
    ) -> ExecutionPlan:
        """从 ProjectStage + StageSkillBinding 生成真实执行计划。

        Args:
            project_id: 项目 ID。
            template_level: 模板级别，为空时尝试使用项目默认值。
            execution_strategy: 执行策略，默认 semi_auto。

        Returns:
            创建好的 ExecutionPlan。
        """
        session = self._session

        proj_stmt = select(ProjectStage).where(
            ProjectStage.project_id == project_id
        ).order_by(ProjectStage.order_index.asc())
        proj_result = await session.execute(proj_stmt)
        stages = list(proj_result.scalars().all())

        skill_nodes: list[dict[str, Any]] = []
        for stage in stages:
            binding_stmt = (
                select(StageSkillBinding)
                .where(StageSkillBinding.project_stage_id == stage.project_stage_id)
                .order_by(StageSkillBinding.execution_order.asc())
            )
            binding_result = await session.execute(binding_stmt)
            bindings = list(binding_result.scalars().all())

            primary_skill_id: str | None = None
            for binding in bindings:
                if binding.role == "primary":
                    primary_skill_id = binding.skill_id
                    break

            for binding in bindings:
                dependencies: list[str] = []
                if binding.role == "auxiliary" and primary_skill_id:
                    dependencies = [primary_skill_id]
                skill_nodes.append(
                    {
                        "skill_id": binding.skill_id,
                        "stage_id": stage.project_stage_id,
                        "node_type": binding.role,
                        "dependencies": dependencies,
                    }
                )

        resolved_template_level = template_level or "Standard"
        return await self.generate_plan(
            project_id=project_id,
            template_level=resolved_template_level,
            skill_nodes=skill_nodes,
            execution_strategy=execution_strategy,
        )

    def _topological_sort(self, skill_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

        queue: deque[str] = deque([sid for sid, deg in in_degree.items() if deg == 0])
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
