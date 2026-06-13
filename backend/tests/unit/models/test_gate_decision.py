"""Tests for GateDecision model."""

from __future__ import annotations

import pytest
from sqlalchemy import select, text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.gate_decision import GateDecision
from app.models.project import Project


class TestGateDecisionModel:
    """GateDecision model tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project for FK constraints."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM gate_decisions"))
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
                application_id="app-gate",
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.mark.asyncio
    async def test_create_gate_decision(self, seeded_project: Project) -> None:
        """Can create a valid gate decision."""
        async with AsyncSessionLocal() as session:
            gate = GateDecision(
                decision_id="gd-001",
                gate_id="gate-1",
                project_id=seeded_project.project_id,
                gate_type="1",
                status="pending",
            )
            session.add(gate)
            await session.commit()

            result = await session.execute(
                select(GateDecision).where(GateDecision.decision_id == "gd-001")
            )
            fetched = result.scalar_one()
            assert fetched.gate_id == "gate-1"
            assert fetched.status == "pending"
            assert fetched.unlocked_stages == "[]"

    @pytest.mark.asyncio
    async def test_unlocked_stages_json(self, seeded_project: Project) -> None:
        """set_unlocked_stages serializes to JSON."""
        async with AsyncSessionLocal() as session:
            gate = GateDecision(
                decision_id="gd-002",
                gate_id="gate-2",
                project_id=seeded_project.project_id,
                gate_type="2",
            )
            gate.set_unlocked_stages(["stage-a", "stage-b"])
            session.add(gate)
            await session.commit()

            result = await session.execute(
                select(GateDecision).where(GateDecision.decision_id == "gd-002")
            )
            fetched = result.scalar_one()
            assert fetched.get_unlocked_stages() == ["stage-a", "stage-b"]
