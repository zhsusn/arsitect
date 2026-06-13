"""Tests for StageOrchestrator."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.execution_plan import ExecutionPlan
from app.models.plan_node import PlanNode
from app.models.project import Project
from app.services.stage_orchestrator import StageOrchestrator


class TestStageOrchestrator:
    """StageOrchestrator tests."""

    @pytest.fixture
    async def seeded_plan(self) -> ExecutionPlan:
        """Seed application, project, execution plan and nodes."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM execution_plan_groups"))
            await session.execute(text("DELETE FROM execution_plan_nodes"))
            await session.execute(text("DELETE FROM bypass_records"))
            await session.execute(text("DELETE FROM execution_plans"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-orch",
                application_name="Orch App",
                local_path="/tmp/orch",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-orch",
                project_name="Orch Project",
                application_id=app.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            plan = ExecutionPlan(
                plan_id="plan-orch",
                project_id=proj.project_id,
                version="v1.0",
                is_frozen=False,
                template_level="Standard",
            )
            session.add(plan)
            await session.commit()
            return plan

    @pytest.mark.asyncio
    async def test_check_stage_readiness_upstream_not_completed(
        self, seeded_plan: ExecutionPlan
    ) -> None:
        """上游未完成时返回 ready=False。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            # 上游节点未完成
            upstream = PlanNode(
                node_id="node-up",
                plan_id=seeded_plan.plan_id,
                skill_id="s-up",
                stage_id="stage-up",
                order_index=0,
                node_type="primary",
                status="EXECUTING",
            )
            session.add(upstream)
            await session.commit()

            orchestrator = StageOrchestrator(
                node_repo=PlanNodeRepository(session),
                group_repo=None,  # type: ignore[arg-type]
            )
            result = await orchestrator.check_stage_readiness(
                stage_id="stage-current",
                plan_id=seeded_plan.plan_id,
                upstream_stages=["stage-up"],
                gate_passed=True,
            )
            assert result.ready is False
            assert result.reason == "上游未完成"

    @pytest.mark.asyncio
    async def test_check_stage_readiness_gate_not_passed(
        self, seeded_plan: ExecutionPlan
    ) -> None:
        """Gate 未通过时返回 ready=False。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            upstream = PlanNode(
                node_id="node-up2",
                plan_id=seeded_plan.plan_id,
                skill_id="s-up2",
                stage_id="stage-up2",
                order_index=0,
                node_type="primary",
                status="COMPLETED",
            )
            session.add(upstream)
            await session.commit()

            orchestrator = StageOrchestrator(
                node_repo=PlanNodeRepository(session),
                group_repo=None,  # type: ignore[arg-type]
            )
            result = await orchestrator.check_stage_readiness(
                stage_id="stage-current",
                plan_id=seeded_plan.plan_id,
                upstream_stages=["stage-up2"],
                gate_passed=False,
            )
            assert result.ready is False
            assert result.reason == "Gate 未通过"

    @pytest.mark.asyncio
    async def test_check_stage_readiness_ready(self, seeded_plan: ExecutionPlan) -> None:
        """上游完成且 Gate 通过时返回 ready=True。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            upstream = PlanNode(
                node_id="node-up3",
                plan_id=seeded_plan.plan_id,
                skill_id="s-up3",
                stage_id="stage-up3",
                order_index=0,
                node_type="primary",
                status="COMPLETED",
            )
            session.add(upstream)
            await session.commit()

            orchestrator = StageOrchestrator(
                node_repo=PlanNodeRepository(session),
                group_repo=None,  # type: ignore[arg-type]
            )
            result = await orchestrator.check_stage_readiness(
                stage_id="stage-current",
                plan_id=seeded_plan.plan_id,
                upstream_stages=["stage-up3"],
                gate_passed=True,
            )
            assert result.ready is True

    @pytest.mark.asyncio
    async def test_schedule_stage_execution(self, seeded_plan: ExecutionPlan) -> None:
        """调度 stage 后节点状态更新为 COMPLETED。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            primary = PlanNode(
                node_id="node-p",
                plan_id=seeded_plan.plan_id,
                skill_id="s-p",
                stage_id="stage-exec",
                order_index=0,
                node_type="primary",
                status="NOT_STARTED",
            )
            aux = PlanNode(
                node_id="node-a",
                plan_id=seeded_plan.plan_id,
                skill_id="s-a",
                stage_id="stage-exec",
                order_index=1,
                node_type="auxiliary",
                status="NOT_STARTED",
            )
            session.add_all([primary, aux])
            await session.commit()

            orchestrator = StageOrchestrator(
                node_repo=PlanNodeRepository(session),
                group_repo=None,  # type: ignore[arg-type]
            )
            result = await orchestrator.schedule_stage_execution(
                stage_id="stage-exec",
                plan_id=seeded_plan.plan_id,
            )
            assert result.status == "COMPLETED"
            assert len(result.node_results) == 2

            refreshed = await PlanNodeRepository(session).list_by_stage(
                seeded_plan.plan_id, "stage-exec"
            )
            for n in refreshed:
                assert n.status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_evaluate_stage_completion_failed(self, seeded_plan: ExecutionPlan) -> None:
        """主 Skill 失败时返回 FAILED。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            primary = PlanNode(
                node_id="node-fail",
                plan_id=seeded_plan.plan_id,
                skill_id="s-fail",
                stage_id="stage-eval",
                order_index=0,
                node_type="primary",
                status="FAILED",
            )
            session.add(primary)
            await session.commit()

            orchestrator = StageOrchestrator(
                node_repo=PlanNodeRepository(session),
                group_repo=None,  # type: ignore[arg-type]
            )
            result = await orchestrator.evaluate_stage_completion(
                stage_id="stage-eval",
                plan_id=seeded_plan.plan_id,
            )
            assert result.completion_status == "FAILED"

    @pytest.mark.asyncio
    async def test_evaluate_stage_completion_completed(self, seeded_plan: ExecutionPlan) -> None:
        """主 Skill 成功 + 所有辅助成功时返回 COMPLETED。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            primary = PlanNode(
                node_id="node-ok",
                plan_id=seeded_plan.plan_id,
                skill_id="s-ok",
                stage_id="stage-eval2",
                order_index=0,
                node_type="primary",
                status="COMPLETED",
            )
            aux = PlanNode(
                node_id="node-ok-a",
                plan_id=seeded_plan.plan_id,
                skill_id="s-ok-a",
                stage_id="stage-eval2",
                order_index=1,
                node_type="auxiliary",
                status="COMPLETED",
            )
            session.add_all([primary, aux])
            await session.commit()

            orchestrator = StageOrchestrator(
                node_repo=PlanNodeRepository(session),
                group_repo=None,  # type: ignore[arg-type]
            )
            result = await orchestrator.evaluate_stage_completion(
                stage_id="stage-eval2",
                plan_id=seeded_plan.plan_id,
            )
            assert result.completion_status == "COMPLETED"
            assert result.warning_count == 0

    @pytest.mark.asyncio
    async def test_evaluate_stage_completion_with_warning(
        self, seeded_plan: ExecutionPlan
    ) -> None:
        """主 Skill 成功 + 辅助存在失败时返回 COMPLETED_WITH_WARNING。"""
        async with AsyncSessionLocal() as session:
            from app.infrastructure.database.repositories.plan_node_repo import (
                PlanNodeRepository,
            )

            primary = PlanNode(
                node_id="node-warn",
                plan_id=seeded_plan.plan_id,
                skill_id="s-warn",
                stage_id="stage-eval3",
                order_index=0,
                node_type="primary",
                status="COMPLETED",
            )
            aux1 = PlanNode(
                node_id="node-warn-a1",
                plan_id=seeded_plan.plan_id,
                skill_id="s-warn-a1",
                stage_id="stage-eval3",
                order_index=1,
                node_type="auxiliary",
                status="COMPLETED",
            )
            aux2 = PlanNode(
                node_id="node-warn-a2",
                plan_id=seeded_plan.plan_id,
                skill_id="s-warn-a2",
                stage_id="stage-eval3",
                order_index=2,
                node_type="auxiliary",
                status="FAILED",
            )
            session.add_all([primary, aux1, aux2])
            await session.commit()

            orchestrator = StageOrchestrator(
                node_repo=PlanNodeRepository(session),
                group_repo=None,  # type: ignore[arg-type]
            )
            result = await orchestrator.evaluate_stage_completion(
                stage_id="stage-eval3",
                plan_id=seeded_plan.plan_id,
            )
            assert result.completion_status == "COMPLETED_WITH_WARNING"
            assert result.warning_count == 1
