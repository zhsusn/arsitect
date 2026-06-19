"""Tests for ExecutionPlanRouter."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.bypass_record import BypassRecord
from app.models.execution_plan import ExecutionPlan
from app.models.plan_node import PlanNode
from app.models.project import Project
from app.models.project_stage import ProjectStage
from app.models.stage_skill_binding import StageSkillBinding
from main import app

client = TestClient(app)


class TestExecutionPlanRouter:
    """ExecutionPlan router tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed application and project."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM execution_plan_groups"))
            await session.execute(text("DELETE FROM execution_plan_nodes"))
            await session.execute(text("DELETE FROM bypass_records"))
            await session.execute(text("DELETE FROM execution_plans"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-ep",
                application_name="EP App",
                local_path="/tmp/ep",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-ep",
                project_name="EP Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.fixture
    async def seeded_plan_with_nodes(
        self, seeded_project: Project
    ) -> tuple[ExecutionPlan, list[PlanNode]]:
        """Seed execution plan with nodes."""
        async with AsyncSessionLocal() as session:
            plan = ExecutionPlan(
                plan_id="plan-ep",
                project_id=seeded_project.project_id,
                version="v1.0",
                is_frozen=False,
                template_level="Standard",
            )
            session.add(plan)
            await session.flush()

            nodes = [
                PlanNode(
                    node_id="n-ep-1",
                    plan_id=plan.plan_id,
                    skill_id="s1",
                    stage_id="st1",
                    order_index=0,
                    node_type="primary",
                    module_id="m1",
                    status="NOT_STARTED",
                ),
                PlanNode(
                    node_id="n-ep-2",
                    plan_id=plan.plan_id,
                    skill_id="s2",
                    stage_id="st1",
                    order_index=1,
                    node_type="auxiliary",
                    module_id="m1",
                    status="NOT_STARTED",
                ),
            ]
            session.add_all(nodes)
            await session.commit()
            return plan, nodes

    @pytest.mark.asyncio
    async def test_create_execution_plan(self, seeded_project: Project) -> None:
        """POST creates execution plan with nodes and groups."""
        payload = {
            "template_level": "Standard",
            "skill_nodes": [
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
            ],
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/execution-plans",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["project_id"] == seeded_project.project_id
        assert data["version"] == "v1.0"
        assert len(data["node_order"]) == 2
        assert len(data["parallel_groups"]) == 2

    @pytest.mark.asyncio
    async def test_validate_execution_plan(
        self, seeded_plan_with_nodes: tuple[ExecutionPlan, list[PlanNode]]
    ) -> None:
        """POST validate returns passed=True for MVP."""
        plan, _ = seeded_plan_with_nodes
        res = client.post(
            f"/api/v1/execution-plans/{plan.plan_id}/validate",
            json=[{"node_id": "n-ep-1", "action": "move_stage"}],
        )
        assert res.status_code == 200
        data = res.json()
        assert data["passed"] is True

    @pytest.mark.asyncio
    async def test_freeze_execution_plan(
        self, seeded_plan_with_nodes: tuple[ExecutionPlan, list[PlanNode]]
    ) -> None:
        """POST freeze sets is_frozen=True."""
        plan, _ = seeded_plan_with_nodes
        res = client.post(f"/api/v1/execution-plans/{plan.plan_id}/freeze")
        assert res.status_code == 200
        data = res.json()
        assert data["is_frozen"] is True

    @pytest.mark.asyncio
    async def test_get_execution_plan(
        self, seeded_plan_with_nodes: tuple[ExecutionPlan, list[PlanNode]]
    ) -> None:
        """GET returns plan details."""
        plan, _ = seeded_plan_with_nodes
        res = client.get(f"/api/v1/execution-plans/{plan.plan_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["plan_id"] == plan.plan_id
        assert "node_order" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_plan(self) -> None:
        """GET unknown plan returns 404."""
        res = client.get("/api/v1/execution-plans/no-such-plan")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_execute_execution_plan(
        self, seeded_plan_with_nodes: tuple[ExecutionPlan, list[PlanNode]]
    ) -> None:
        """POST execute schedules first stage."""
        plan, _ = seeded_plan_with_nodes
        res = client.post(f"/api/v1/execution-plans/{plan.plan_id}/execute")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "COMPLETED"
        assert len(data["node_results"]) == 2

    @pytest.mark.asyncio
    async def test_get_execution_status(
        self, seeded_plan_with_nodes: tuple[ExecutionPlan, list[PlanNode]]
    ) -> None:
        """GET status returns node statuses."""
        plan, _ = seeded_plan_with_nodes
        res = client.get(f"/api/v1/execution-plans/{plan.plan_id}/status")
        assert res.status_code == 200
        data = res.json()
        assert data["execution_id"] == plan.plan_id
        assert len(data["nodes"]) == 2

    @pytest.mark.asyncio
    async def test_create_bypass(
        self, seeded_plan_with_nodes: tuple[ExecutionPlan, list[PlanNode]]
    ) -> None:
        """POST bypass creates a bypass record."""
        plan, _ = seeded_plan_with_nodes
        payload = {
            "stage_id": "st1",
            "skill_id": "s1",
            "authorization_token": "a" * 32,
            "acknowledged": True,
            "reason": "紧急执行变更",
        }
        res = client.post(
            f"/api/v1/executions/{plan.plan_id}/bypass",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["plan_id"] == plan.plan_id
        assert data["status"] == "PENDING_POST_APPROVAL"

    @pytest.mark.asyncio
    async def test_list_bypass_records(
        self, seeded_plan_with_nodes: tuple[ExecutionPlan, list[PlanNode]]
    ) -> None:
        """GET bypass-status returns bypass records."""
        plan, _ = seeded_plan_with_nodes
        async with AsyncSessionLocal() as session:
            record = BypassRecord(
                record_id="rec-ep-1",
                plan_id=plan.plan_id,
                stage_id="st1",
                skill_id="s1",
                triggered_by="user-1",
                authorizer_token="a" * 32,
                reason="test reason",
                status="PENDING_POST_APPROVAL",
                deadline_at=datetime.utcnow() + timedelta(hours=24),
            )
            session.add(record)
            await session.commit()

        res = client.get(f"/api/v1/executions/{plan.plan_id}/bypass-status")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert any(r["record_id"] == "rec-ep-1" for r in data)

    @pytest.fixture
    async def seeded_project_with_bindings(
        self, seeded_project: Project
    ) -> Project:
        """Seed project stages and skill bindings."""
        async with AsyncSessionLocal() as session:
            stage1 = ProjectStage(
                project_stage_id="ps-ep-1",
                project_id=seeded_project.project_id,
                stage_id="ts-ep-1",
                order_index=1,
                status="DEFINED",
                primary_skill_id="skill-ep-1",
                runtime_status="not_started",
                is_gate_required=False,
            )
            stage2 = ProjectStage(
                project_stage_id="ps-ep-2",
                project_id=seeded_project.project_id,
                stage_id="ts-ep-2",
                order_index=2,
                status="DEFINED",
                primary_skill_id="skill-ep-2",
                runtime_status="not_started",
                is_gate_required=False,
            )
            session.add_all([stage1, stage2])
            await session.flush()

            session.add(
                StageSkillBinding(
                    binding_id="b-ep-1",
                    project_stage_id=stage1.project_stage_id,
                    skill_id="skill-ep-1",
                    role="primary",
                    execution_order=0,
                )
            )
            session.add(
                StageSkillBinding(
                    binding_id="b-ep-2",
                    project_stage_id=stage1.project_stage_id,
                    skill_id="skill-ep-aux",
                    role="auxiliary",
                    execution_order=1,
                )
            )
            session.add(
                StageSkillBinding(
                    binding_id="b-ep-3",
                    project_stage_id=stage2.project_stage_id,
                    skill_id="skill-ep-2",
                    role="primary",
                    execution_order=0,
                )
            )
            await session.commit()
            return seeded_project

    @pytest.mark.asyncio
    async def test_create_execution_plan_from_project_bindings(
        self, seeded_project_with_bindings: Project
    ) -> None:
        """POST with empty skill_nodes generates plan from project bindings."""
        payload = {"template_level": None, "skill_nodes": []}
        res = client.post(
            f"/api/v1/projects/{seeded_project_with_bindings.project_id}/execution-plans",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["project_id"] == seeded_project_with_bindings.project_id
        assert data["template_level"] == seeded_project_with_bindings.template_level
        assert len(data["node_order"]) == 3
        assert len(data["parallel_groups"]) == 3
        assert len(data["dependency_matrix"]) == 3
        # Auxiliary node depends on primary node in the same stage.
        auxiliary_nodes = [n for n in data["nodes"] if n["node_type"] == "auxiliary"]
        assert len(auxiliary_nodes) == 1
        primary_nodes = [n for n in data["nodes"] if n["node_type"] == "primary"]
        assert len(primary_nodes) == 2
        aux_node = auxiliary_nodes[0]
        primary_in_stage = next(
            n for n in primary_nodes if n["stage_id"] == aux_node["stage_id"]
        )
        assert data["dependency_matrix"][aux_node["node_id"]] == [primary_in_stage["node_id"]]
