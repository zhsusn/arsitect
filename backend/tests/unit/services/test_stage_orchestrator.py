"""Tests for StageOrchestrator."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select, text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.artifact import ArtifactFile
from app.models.execution_plan import ExecutionPlan
from app.models.plan_node import PlanNode
from app.models.project import Project
from app.models.project_path_config import ProjectPathConfig
from app.models.project_stage import ProjectStage
from app.models.skill_execution import SkillExecution
from app.models.stage_rollback_log import StageRollbackLog
from app.models.stage_skill_binding import StageSkillBinding
from app.models.template import Template
from app.models.template_stage import TemplateStage
from app.services.pocketflow.cli_adapter import MockCLIAdapter
from app.services.pocketflow.engine import PocketFlowEngine
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
    async def test_check_stage_readiness_gate_not_passed(self, seeded_plan: ExecutionPlan) -> None:
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
    async def test_evaluate_stage_completion_with_warning(self, seeded_plan: ExecutionPlan) -> None:
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



@pytest.fixture
def mock_pocketflow_engine() -> PocketFlowEngine:
    """PocketFlow engine using an in-memory CLI adapter for tests."""
    return PocketFlowEngine(cli_adapter=MockCLIAdapter())


class TestProjectStageOrchestrator:
    """Tests for project-stage runtime state machine methods."""

    @pytest.fixture
    async def seeded_project_stages(self) -> str:
        """Seed a project with two stages and skill bindings."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM stage_skill_bindings"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM project_path_config"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

            app = Application(
                application_id="app-proj-orch",
                application_name="Proj Orch App",
                local_path="/tmp/proj-orch",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-proj-orch",
                project_name="Proj Orch Project",
                application_id=app.application_id,
                template_level="Standard",
                execution_strategy="semi_auto",
            )
            session.add(proj)
            await session.flush()

            stage1 = ProjectStage(
                project_stage_id="ps-1",
                project_id=proj.project_id,
                stage_id="ts-1",
                order_index=1,
                status="DEFINED",
                primary_skill_id="brainstorming",
                runtime_status="ready",
                is_gate_required=True,
                auto_advance=False,
                execution_strategy="semi_auto",
            )
            stage2 = ProjectStage(
                project_stage_id="ps-2",
                project_id=proj.project_id,
                stage_id="ts-2",
                order_index=2,
                status="DEFINED",
                primary_skill_id="requirement-analysis",
                runtime_status="not_started",
                is_gate_required=True,
                auto_advance=False,
                execution_strategy="semi_auto",
            )
            session.add_all([stage1, stage2])
            await session.flush()

            session.add(
                StageSkillBinding(
                    binding_id="b-1",
                    project_stage_id=stage1.project_stage_id,
                    skill_id="brainstorming",
                    role="primary",
                    execution_order=0,
                    is_optional=False,
                )
            )
            session.add(
                StageSkillBinding(
                    binding_id="b-2",
                    project_stage_id=stage2.project_stage_id,
                    skill_id="requirement-analysis",
                    role="primary",
                    execution_order=0,
                    is_optional=False,
                )
            )
            await session.commit()
            return proj.project_id

    @pytest.mark.asyncio
    async def test_execute_stage_transitions_to_review_pending(
        self, seeded_project_stages: str, mock_pocketflow_engine: PocketFlowEngine
    ) -> None:
        """semi_auto 下阶段执行后进入 review_pending。"""
        async with AsyncSessionLocal() as session:
            orchestrator = StageOrchestrator(
                session=session, pocketflow_engine=mock_pocketflow_engine
            )
            result = await orchestrator.execute_stage("ps-1")
            assert result["status"] == "review_pending"
            assert result["project_stage_id"] == "ps-1"

    @pytest.mark.asyncio
    async def test_advance_stage_unlocks_next_stage(
        self, seeded_project_stages: str, mock_pocketflow_engine: PocketFlowEngine
    ) -> None:
        """Gate 通过后推进到下一阶段并将其置为 READY。"""
        async with AsyncSessionLocal() as session:
            orchestrator = StageOrchestrator(
                session=session, pocketflow_engine=mock_pocketflow_engine
            )
            await orchestrator.execute_stage("ps-1")
            advanced = await orchestrator.advance_stage("ps-1")
            assert advanced["status"] == "passed"
            assert advanced["next_stage_id"] == "ps-2"

            stage2 = await session.get(ProjectStage, "ps-2")
            assert stage2 is not None
            assert stage2.runtime_status == "ready"

    @pytest.mark.asyncio
    async def test_gate_reject_blocks_stage(
        self, seeded_project_stages: str, mock_pocketflow_engine: PocketFlowEngine
    ) -> None:
        """Gate 驳回后阶段进入 blocked。"""
        async with AsyncSessionLocal() as session:
            orchestrator = StageOrchestrator(
                session=session, pocketflow_engine=mock_pocketflow_engine
            )
            await orchestrator.execute_stage("ps-1")
            result = await orchestrator.decide_gate("ps-1", "reject", "需要修改")
            assert result["status"] == "blocked"

    @pytest.mark.asyncio
    async def test_get_stage_progress(
        self, seeded_project_stages: str
    ) -> None:
        """阶段进度聚合正确。"""
        async with AsyncSessionLocal() as session:
            orchestrator = StageOrchestrator(session=session)
            progress = await orchestrator.get_stage_progress(seeded_project_stages)
            assert progress["project_id"] == seeded_project_stages
            assert len(progress["stages"]) == 2
            assert progress["stages"][0]["runtime_status"] == "ready"

    @pytest.mark.asyncio
    async def test_stage_status_changed_event_published(
        self, seeded_project_stages: str, mock_pocketflow_engine: PocketFlowEngine
    ) -> None:
        """阶段状态变更时发布 stage.status_changed 事件。"""

        class _EventCollector:
            def __init__(self) -> None:
                self.events: list[Any] = []

            def publish(self, event: Any) -> None:
                self.events.append(event)

        collector = _EventCollector()
        async with AsyncSessionLocal() as session:
            orchestrator = StageOrchestrator(
                session=session,
                event_bus=collector,
                pocketflow_engine=mock_pocketflow_engine,
            )
            await orchestrator.execute_stage("ps-1")

        status_events = [
            e for e in collector.events if e.event_type == "stage.status_changed"
        ]
        assert len(status_events) >= 1
        payload = status_events[0].payload
        assert payload["old_status"] == "ready"
        assert payload["new_status"] == "in_progress"
        assert payload["stage_id"] == "ps-1"


class TestStageOrchestratorEventsAndRollback:
    """Tests for event publishing and stage rollback."""

    @pytest.fixture
    async def seeded_rollback_project(self) -> str:
        """Seed a project with three stages, bindings, and artifacts."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM artifact_files"))
            await session.execute(text("DELETE FROM stage_rollback_logs"))
            await session.execute(text("DELETE FROM stage_skill_bindings"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM project_path_config"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

            app = Application(
                application_id="app-rollback",
                application_name="Rollback App",
                local_path="/tmp/rollback",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-rollback",
                project_name="Rollback Project",
                application_id=app.application_id,
                template_level="Standard",
                execution_strategy="semi_auto",
            )
            session.add(proj)
            await session.flush()

            stages: list[ProjectStage] = []
            for idx, (ps_id, sk_id) in enumerate(
                [("ps-r1", "skill-r1"), ("ps-r2", "skill-r2"), ("ps-r3", "skill-r3")],
                start=1,
            ):
                stage = ProjectStage(
                    project_stage_id=ps_id,
                    project_id=proj.project_id,
                    stage_id=f"ts-r{idx}",
                    order_index=idx,
                    status="DEFINED",
                    primary_skill_id=sk_id,
                    runtime_status="passed" if idx == 1 else "not_started",
                    is_gate_required=False,
                    auto_advance=False,
                    execution_strategy="semi_auto",
                )
                stages.append(stage)
                session.add(stage)
            await session.flush()

            for stage in stages:
                session.add(
                    StageSkillBinding(
                        binding_id=f"b-{stage.project_stage_id}",
                        project_stage_id=stage.project_stage_id,
                        skill_id=stage.primary_skill_id or "",
                        role="primary",
                        execution_order=0,
                        is_optional=False,
                    )
                )

            for stage in stages[1:]:
                session.add(
                    ArtifactFile(
                        artifact_id=f"art-{stage.project_stage_id}",
                        project_id=proj.project_id,
                        stage_id=stage.project_stage_id,
                        file_name=f"{stage.project_stage_id}.md",
                        file_path=f"/tmp/{stage.project_stage_id}.md",
                        file_type="md",
                    )
                )
            await session.commit()
            return proj.project_id

    @pytest.mark.asyncio
    async def test_rollback_stage_resets_downstream_and_marks_artifacts_stale(
        self, seeded_rollback_project: str
    ) -> None:
        """回滚到第一阶段后，下游阶段重置且产物被标记为过期。"""
        async with AsyncSessionLocal() as session:
            orchestrator = StageOrchestrator(session=session)
            result = await orchestrator.rollback_stage(
                project_stage_id="ps-r2",
                target_stage_id="ps-r1",
                reason="需要重做",
            )
            assert result["project_id"] == seeded_rollback_project
            assert result["target_stage_id"] == "ps-r1"
            assert "ps-r2" in result["reset_stage_ids"]
            assert "ps-r3" in result["reset_stage_ids"]
            assert "art-ps-r2" in result["stale_artifact_ids"]
            assert "art-ps-r3" in result["stale_artifact_ids"]

            stage2 = await session.get(ProjectStage, "ps-r2")
            assert stage2 is not None
            assert stage2.runtime_status == "not_started"
            stage3 = await session.get(ProjectStage, "ps-r3")
            assert stage3 is not None
            assert stage3.runtime_status == "not_started"
            stage1 = await session.get(ProjectStage, "ps-r1")
            assert stage1 is not None
            assert stage1.runtime_status == "ready"

            art2 = await session.get(ArtifactFile, "art-ps-r2")
            assert art2 is not None
            assert art2.stale_flag is True

            logs = await session.execute(
                select(StageRollbackLog).where(
                    StageRollbackLog.project_id == seeded_rollback_project
                )
            )
            rollback_log = logs.scalar_one_or_none()
            assert rollback_log is not None
            assert rollback_log.from_stage_id == "ps-r2"
            assert rollback_log.to_stage_id == "ps-r1"



    @pytest.fixture
    async def seeded_full_auto_project(self) -> str:
        """Seed a full_auto project with three stages and bindings."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM artifact_files"))
            await session.execute(text("DELETE FROM stage_rollback_logs"))
            await session.execute(text("DELETE FROM stage_skill_bindings"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM project_path_config"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

            app = Application(
                application_id="app-auto",
                application_name="Auto Advance App",
                local_path="/tmp/auto",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-auto",
                project_name="Auto Advance Project",
                application_id=app.application_id,
                template_level="Standard",
                execution_strategy="full_auto",
            )
            session.add(proj)
            await session.flush()

            real_skills = ["brainstorming", "requirement-analysis", "project-size-estimate"]
            stages: list[ProjectStage] = []
            for idx, (ps_id, sk_id) in enumerate(
                [("ps-a1", real_skills[0]), ("ps-a2", real_skills[1]), ("ps-a3", real_skills[2])],
                start=1,
            ):
                stage = ProjectStage(
                    project_stage_id=ps_id,
                    project_id=proj.project_id,
                    stage_id=f"ts-a{idx}",
                    order_index=idx,
                    status="DEFINED",
                    primary_skill_id=sk_id,
                    runtime_status="ready" if idx == 1 else "not_started",
                    is_gate_required=False,
                    auto_advance=False,
                    execution_strategy="full_auto",
                )
                stages.append(stage)
                session.add(stage)
            await session.flush()

            for stage in stages:
                session.add(
                    StageSkillBinding(
                        binding_id=f"b-{stage.project_stage_id}",
                        project_stage_id=stage.project_stage_id,
                        skill_id=stage.primary_skill_id or "",
                        role="primary",
                        execution_order=0,
                        is_optional=False,
                    )
                )
            await session.commit()
            return proj.project_id

    @pytest.mark.asyncio
    async def test_auto_advance_event_published_in_full_auto(
        self,
        seeded_full_auto_project: str,
        mock_pocketflow_engine: PocketFlowEngine,
    ) -> None:
        """full_auto 策略下阶段完成后自动推进并发布 stage.auto_advance 事件。"""

        class _EventCollector:
            def __init__(self) -> None:
                self.events: list[Any] = []

            def publish(self, event: Any) -> None:
                self.events.append(event)

        collector = _EventCollector()
        async with AsyncSessionLocal() as session:
            orchestrator = StageOrchestrator(
                session=session,
                event_bus=collector,
                pocketflow_engine=mock_pocketflow_engine,
            )
            await orchestrator.execute_stage("ps-a1")

        auto_advance_events = [
            e for e in collector.events if e.event_type == "stage.auto_advance"
        ]
        assert len(auto_advance_events) >= 1
        payload = auto_advance_events[0].payload
        assert payload["from_stage_id"] == "ps-a1"
        assert payload["to_stage_id"] == "ps-a2"


class TestStageOrchestratorProgress:
    """Tests for get_stage_progress merge group enrichment."""

    @pytest.fixture
    async def seeded_progress_project(self) -> str:
        """Seed a project with TemplateStage and ProjectPathConfig."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM stage_skill_bindings"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM project_path_config"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

            app = Application(
                application_id="app-progress",
                application_name="Progress App",
                local_path="/tmp/progress",
            )
            session.add(app)
            await session.flush()

            tpl = Template(
                template_id="Light",
                template_name="轻量",
                description="Light template",
                stage_count=1,
                estimated_skill_count=1,
                applicable_complexity="Light",
                default_execution_strategy="semi_auto",
                merge_policy_json='{"groups": [{"group_id": "g3", "label": "需求对齐", "business_stage_keys": ["clarify", "align"], "gate_at_end": true, "auto_advance": true}]}',
            )
            session.add(tpl)
            await session.flush()

            proj = Project(
                project_id="proj-progress",
                project_name="Progress Project",
                application_id=app.application_id,
                template_level="Light",
                execution_strategy="semi_auto",
                merge_policy_json=tpl.merge_policy_json,
            )
            session.add(proj)
            await session.flush()

            session.add(
                ProjectPathConfig(
                    config_id="cfg-progress",
                    project_id=proj.project_id,
                    template_level="Light",
                    execution_strategy="semi_auto",
                    merge_policy_json=proj.merge_policy_json,
                )
            )

            template_stage = TemplateStage(
                stage_id="ts-align",
                stage_name="需求对齐",
                business_stage_key="align",
                order_index=1,
                template_id="Light",
                primary_skill_id="prd-generation",
            )
            session.add(template_stage)
            await session.flush()

            stage = ProjectStage(
                project_stage_id="ps-progress-1",
                project_id=proj.project_id,
                stage_id="align",
                order_index=1,
                status="DEFINED",
                primary_skill_id="prd-generation",
                runtime_status="in_progress",
                is_gate_required=True,
                auto_advance=False,
                execution_strategy="semi_auto",
            )
            session.add(stage)
            await session.commit()
            return proj.project_id

    @pytest.mark.asyncio
    async def test_get_stage_progress_includes_merge_group(
        self, seeded_progress_project: str
    ) -> None:
        """get_stage_progress returns business_stage_key and merge group info."""
        async with AsyncSessionLocal() as session:
            orchestrator = StageOrchestrator(session=session)
            progress = await orchestrator.get_stage_progress(seeded_progress_project)

        assert progress["project_id"] == seeded_progress_project
        assert len(progress["stages"]) == 1
        stage_item = progress["stages"][0]
        assert stage_item["business_stage_key"] == "align"
        assert stage_item["merge_group_label"] == "需求对齐"
        assert set(stage_item["merged_stage_keys"]) == {"clarify", "align"}


class TestRealSkillExecution:
    """Tests that StageOrchestrator delegates to PocketFlowEngine."""

    @pytest.fixture
    async def seeded_real_skill_project(self) -> str:
        """Seed a project whose stage binds a real local skill."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM stage_skill_bindings"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM project_path_config"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

            app = Application(
                application_id="app-real",
                application_name="Real Skill App",
                local_path="/tmp/real",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-real",
                project_name="Real Skill Project",
                application_id=app.application_id,
                template_level="Standard",
                execution_strategy="semi_auto",
            )
            session.add(proj)
            await session.flush()

            stage = ProjectStage(
                project_stage_id="ps-real",
                project_id=proj.project_id,
                stage_id="brainstorm",
                order_index=1,
                status="DEFINED",
                primary_skill_id="brainstorming",
                runtime_status="ready",
                is_gate_required=False,
                auto_advance=False,
                execution_strategy="semi_auto",
            )
            session.add(stage)
            await session.flush()

            session.add(
                StageSkillBinding(
                    binding_id="b-real",
                    project_stage_id=stage.project_stage_id,
                    skill_id="brainstorming",
                    role="primary",
                    execution_order=0,
                    is_optional=False,
                )
            )
            await session.commit()
            return proj.project_id

    @pytest.mark.asyncio
    async def test_execute_stage_runs_skill_via_engine(
        self,
        seeded_real_skill_project: str,
        mock_pocketflow_engine: PocketFlowEngine,
    ) -> None:
        """execute_stage runs the bound skill through the injected engine."""
        async with AsyncSessionLocal() as session:
            orchestrator = StageOrchestrator(
                session=session,
                pocketflow_engine=mock_pocketflow_engine,
            )
            result = await orchestrator.execute_stage("ps-real")

        assert result["status"] == "passed"
        assert result["project_stage_id"] == "ps-real"

    @pytest.mark.asyncio
    async def test_execute_stage_blocks_on_skill_failure(
        self,
        seeded_real_skill_project: str,
    ) -> None:
        """Skill failure transitions the stage to blocked."""
        from app.services.pocketflow.cli_adapter import CLIExecutionResult, ExecutionStatus

        failing_result = CLIExecutionResult(
            skill_id="brainstorming",
            status=ExecutionStatus.ERROR,
            exit_code=1,
            stdout="",
            stderr="skill failed",
            duration_ms=10,
        )
        engine = PocketFlowEngine(
            cli_adapter=MockCLIAdapter(result=failing_result)
        )

        async with AsyncSessionLocal() as session:
            orchestrator = StageOrchestrator(
                session=session,
                pocketflow_engine=engine,
            )
            result = await orchestrator.execute_stage("ps-real")

        assert result["status"] == "blocked"
        assert "skill failed" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_skill_execution_records_updated(
        self,
        seeded_real_skill_project: str,
        mock_pocketflow_engine: PocketFlowEngine,
    ) -> None:
        """SkillExecution rows are updated after running the skill."""
        async with AsyncSessionLocal() as session:
            orchestrator = StageOrchestrator(
                session=session,
                pocketflow_engine=mock_pocketflow_engine,
            )
            await orchestrator.execute_stage("ps-real")

            result = await session.execute(
                select(SkillExecution).where(SkillExecution.stage_id == "ps-real")
            )
            execution = result.scalar_one()
            assert execution.overall_status == "SUCCESS"
            assert execution.phase_status == "COMPLETED"
            assert execution.completed_at is not None
