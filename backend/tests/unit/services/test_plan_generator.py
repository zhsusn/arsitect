"""Tests for ExecutionPlanGenerator."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.exceptions import ValidationError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.services.execution_plan_generator import ExecutionPlanGenerator


class TestExecutionPlanGenerator:
    """ExecutionPlanGenerator tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM execution_plan_groups"))
            await session.execute(text("DELETE FROM execution_plan_nodes"))
            await session.execute(text("DELETE FROM bypass_records"))
            await session.execute(text("DELETE FROM execution_plans"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-gen",
                application_name="Gen App",
                local_path="/tmp/gen",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-gen",
                project_name="Gen Project",
                application_id=app.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.mark.asyncio
    async def test_generate_plan_topological_sort(self, seeded_project: Project) -> None:
        """生成计划并按拓扑排序分配 order_index。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.execution_plan_repo import (
                ExecutionPlanRepository,
            )
            from app.infrastructure.database.repositories.parallel_group_repo import (
                ParallelGroupRepository,
            )
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            generator = ExecutionPlanGenerator(
                plan_repo=ExecutionPlanRepository(session),
                node_repo=PlanNodeRepository(session),
                group_repo=ParallelGroupRepository(session),
            )
            skill_nodes = [
                {
                    "skill_id": "s2",
                    "stage_id": "st1",
                    "node_type": "auxiliary",
                    "dependencies": ["s1"],
                    "module_id": "m1",
                },
                {
                    "skill_id": "s1",
                    "stage_id": "st1",
                    "node_type": "primary",
                    "dependencies": [],
                    "module_id": "m1",
                },
            ]
            plan = await generator.generate_plan(
                project_id=seeded_project.project_id,
                template_level="Standard",
                skill_nodes=skill_nodes,
            )
            assert plan.project_id == seeded_project.project_id
            assert plan.version == "v1.0"

            nodes = await PlanNodeRepository(session).list_by_plan(plan.plan_id)
            assert len(nodes) == 2
            # s1 应该在 s2 之前
            assert nodes[0].skill_id == "s1"
            assert nodes[1].skill_id == "s2"
            assert nodes[0].order_index < nodes[1].order_index

    @pytest.mark.asyncio
    async def test_cycle_detection(self, seeded_project: Project) -> None:
        """检测到环时抛出 PLAN_CYCLE_DETECTED。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.execution_plan_repo import (
                ExecutionPlanRepository,
            )
            from app.infrastructure.database.repositories.parallel_group_repo import (
                ParallelGroupRepository,
            )
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            generator = ExecutionPlanGenerator(
                plan_repo=ExecutionPlanRepository(session),
                node_repo=PlanNodeRepository(session),
                group_repo=ParallelGroupRepository(session),
            )
            skill_nodes = [
                {
                    "skill_id": "s1",
                    "stage_id": "st1",
                    "node_type": "primary",
                    "dependencies": ["s2"],
                    "module_id": "m1",
                },
                {
                    "skill_id": "s2",
                    "stage_id": "st1",
                    "node_type": "auxiliary",
                    "dependencies": ["s1"],
                    "module_id": "m1",
                },
            ]
            with pytest.raises(ValidationError, match="PLAN_CYCLE_DETECTED"):
                await generator.generate_plan(
                    project_id=seeded_project.project_id,
                    template_level="Standard",
                    skill_nodes=skill_nodes,
                )

    @pytest.mark.asyncio
    async def test_multiple_primary_rejected(self, seeded_project: Project) -> None:
        """同一 stage 存在多个 primary 时抛出 PLAN_MULTIPLE_PRIMARY。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.execution_plan_repo import (
                ExecutionPlanRepository,
            )
            from app.infrastructure.database.repositories.parallel_group_repo import (
                ParallelGroupRepository,
            )
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            generator = ExecutionPlanGenerator(
                plan_repo=ExecutionPlanRepository(session),
                node_repo=PlanNodeRepository(session),
                group_repo=ParallelGroupRepository(session),
            )
            skill_nodes = [
                {
                    "skill_id": "s1",
                    "stage_id": "st1",
                    "node_type": "primary",
                    "dependencies": [],
                    "module_id": "m1",
                },
                {
                    "skill_id": "s2",
                    "stage_id": "st1",
                    "node_type": "primary",
                    "dependencies": [],
                    "module_id": "m1",
                },
            ]
            with pytest.raises(ValidationError, match="PLAN_MULTIPLE_PRIMARY"):
                await generator.generate_plan(
                    project_id=seeded_project.project_id,
                    template_level="Standard",
                    skill_nodes=skill_nodes,
                )

    @pytest.mark.asyncio
    async def test_zero_primary_rejected(self, seeded_project: Project) -> None:
        """同一 stage 没有 primary 时抛出 PLAN_MULTIPLE_PRIMARY。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.execution_plan_repo import (
                ExecutionPlanRepository,
            )
            from app.infrastructure.database.repositories.parallel_group_repo import (
                ParallelGroupRepository,
            )
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            generator = ExecutionPlanGenerator(
                plan_repo=ExecutionPlanRepository(session),
                node_repo=PlanNodeRepository(session),
                group_repo=ParallelGroupRepository(session),
            )
            skill_nodes = [
                {
                    "skill_id": "s1",
                    "stage_id": "st1",
                    "node_type": "auxiliary",
                    "dependencies": [],
                    "module_id": "m1",
                },
            ]
            with pytest.raises(ValidationError, match="PLAN_MULTIPLE_PRIMARY"):
                await generator.generate_plan(
                    project_id=seeded_project.project_id,
                    template_level="Standard",
                    skill_nodes=skill_nodes,
                )

    @pytest.mark.asyncio
    async def test_parallel_groups_created(self, seeded_project: Project) -> None:
        """正确创建 primary_serial 和 auxiliary_parallel 分组。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.execution_plan_repo import (
                ExecutionPlanRepository,
            )
            from app.infrastructure.database.repositories.parallel_group_repo import (
                ParallelGroupRepository,
            )
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            generator = ExecutionPlanGenerator(
                plan_repo=ExecutionPlanRepository(session),
                node_repo=PlanNodeRepository(session),
                group_repo=ParallelGroupRepository(session),
            )
            skill_nodes = [
                {
                    "skill_id": "s1",
                    "stage_id": "st1",
                    "node_type": "primary",
                    "dependencies": [],
                    "module_id": "m1",
                },
                {
                    "skill_id": "s2",
                    "stage_id": "st1",
                    "node_type": "auxiliary",
                    "dependencies": ["s1"],
                    "module_id": "m1",
                },
                {
                    "skill_id": "s3",
                    "stage_id": "st1",
                    "node_type": "auxiliary",
                    "dependencies": ["s1"],
                    "module_id": "m1",
                },
            ]
            plan = await generator.generate_plan(
                project_id=seeded_project.project_id,
                template_level="Standard",
                skill_nodes=skill_nodes,
            )
            groups = await ParallelGroupRepository(session).list_by_plan(plan.plan_id)
            assert len(groups) == 2
            types = {g.group_type for g in groups}
            assert "primary_serial" in types
            assert "auxiliary_parallel" in types
