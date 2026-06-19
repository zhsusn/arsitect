"""Tests for StageGateController."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.project_stage import ProjectStage
from app.services.stage_gate_controller import StageGateController


class TestStageGateController:
    """StageGateController unit tests."""

    @pytest.fixture
    async def seeded_stage(self) -> ProjectStage:
        """Seed an application, project and project stage."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM gate_decisions"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-gate",
                application_name="Gate App",
                local_path="/tmp/gate",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-gate",
                project_name="Gate Project",
                application_id=app.application_id,
                template_level="Standard",
                execution_strategy="semi_auto",
            )
            session.add(proj)
            await session.flush()

            stage = ProjectStage(
                project_stage_id="ps-gate-1",
                project_id=proj.project_id,
                stage_id="stage-1",
                order_index=1,
                status="DEFINED",
                runtime_status="gate_pending",
                primary_skill_id="skill-1",
                execution_strategy="semi_auto",
            )
            session.add(stage)
            await session.commit()
            return stage

    @pytest.mark.asyncio
    async def test_create_gate(self, seeded_stage: ProjectStage) -> None:
        """Can create a pending gate for a stage."""
        async with AsyncSessionLocal() as session:
            controller = StageGateController(session)
            gate = await controller.create_gate(
                seeded_stage.project_stage_id,
                seeded_stage.project_id,
                gate_type="2",
                reason="等待确认",
            )
            assert gate.gate_id == seeded_stage.project_stage_id
            assert gate.status == "pending"
            assert gate.gate_type == "2"

    @pytest.mark.asyncio
    async def test_create_gate_idempotent(self, seeded_stage: ProjectStage) -> None:
        """Creating a gate twice returns the existing pending gate."""
        async with AsyncSessionLocal() as session:
            controller = StageGateController(session)
            first = await controller.create_gate(
                seeded_stage.project_stage_id, seeded_stage.project_id
            )
            second = await controller.create_gate(
                seeded_stage.project_stage_id, seeded_stage.project_id
            )
            assert first.decision_id == second.decision_id

    @pytest.mark.asyncio
    async def test_decide_pass(self, seeded_stage: ProjectStage) -> None:
        """Pass decision resolves gate to passed."""
        async with AsyncSessionLocal() as session:
            controller = StageGateController(session)
            await controller.create_gate(seeded_stage.project_stage_id, seeded_stage.project_id)
            decided = await controller.decide(
                seeded_stage.project_stage_id, "pass", "operator-1", "LGTM"
            )
            assert decided.status == "passed"
            assert decided.decision_by == "operator-1"
            assert decided.reason == "LGTM"
            assert decided.duration_sec is not None

    @pytest.mark.asyncio
    async def test_decide_reject(self, seeded_stage: ProjectStage) -> None:
        """Reject decision resolves gate to rejected."""
        async with AsyncSessionLocal() as session:
            controller = StageGateController(session)
            await controller.create_gate(seeded_stage.project_stage_id, seeded_stage.project_id)
            decided = await controller.decide(
                seeded_stage.project_stage_id, "reject", "operator-2", "需要修改"
            )
            assert decided.status == "rejected"
            assert decided.reason == "需要修改"

    @pytest.mark.asyncio
    async def test_get_pending_gate(self, seeded_stage: ProjectStage) -> None:
        """Can retrieve the latest pending gate."""
        async with AsyncSessionLocal() as session:
            controller = StageGateController(session)
            created = await controller.create_gate(
                seeded_stage.project_stage_id, seeded_stage.project_id
            )
            fetched = await controller.get_pending_gate(seeded_stage.project_stage_id)
            assert fetched is not None
            assert fetched.decision_id == created.decision_id

    @pytest.mark.asyncio
    async def test_list_by_project(self, seeded_stage: ProjectStage) -> None:
        """Can list gate decisions for a project."""
        async with AsyncSessionLocal() as session:
            controller = StageGateController(session)
            await controller.create_gate(seeded_stage.project_stage_id, seeded_stage.project_id)
            gates = await controller.list_by_project(seeded_stage.project_id)
            assert len(gates) == 1
            assert gates[0].project_id == seeded_stage.project_id
