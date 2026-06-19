"""Tests for GateRouter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.gate_decision import GateDecision
from app.models.project import Project
from main import app

client = TestClient(app)


class TestGateRouter:
    """GateRouter integration tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM gate_decisions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-router-gate",
                application_name="Router Gate App",
                local_path="/tmp/router-gate",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-router-gate",
                project_name="Router Gate Project",
                application_id="app-router-gate",
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.mark.asyncio
    async def test_list_gates(self, seeded_project: Project) -> None:
        """GET /gates returns paginated gate decisions."""
        async with AsyncSessionLocal() as session:
            gate = GateDecision(
                decision_id="gd-r1",
                gate_id="gate-r1",
                project_id=seeded_project.project_id,
                gate_type="1",
            )
            session.add(gate)
            await session.commit()

        res = client.get(f"/api/v1/gates?project_id={seeded_project.project_id}")
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
        assert any(g["decision_id"] == "gd-r1" for g in data["data"])

    @pytest.mark.asyncio
    async def test_get_gate(self, seeded_project: Project) -> None:
        """GET /gates/{id} returns gate details."""
        async with AsyncSessionLocal() as session:
            gate = GateDecision(
                decision_id="gd-r2",
                gate_id="gate-r2",
                project_id=seeded_project.project_id,
                gate_type="2",
            )
            session.add(gate)
            await session.commit()

        res = client.get("/api/v1/gates/gd-r2")
        assert res.status_code == 200
        data = res.json()
        assert data["gate_id"] == "gate-r2"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, seeded_project: Project) -> None:
        """GET unknown gate returns 404."""
        res = client.get("/api/v1/gates/no-such-gate")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_approve_gate(self, seeded_project: Project) -> None:
        """POST /approve passes the gate."""
        async with AsyncSessionLocal() as session:
            gate = GateDecision(
                decision_id="gd-r3",
                gate_id="gate-r3",
                project_id=seeded_project.project_id,
                gate_type="1",
                status="pending",
            )
            session.add(gate)
            await session.commit()

        res = client.post("/api/v1/gates/gd-r3/approve")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "passed"

    @pytest.mark.asyncio
    async def test_reject_gate(self, seeded_project: Project) -> None:
        """POST /reject rejects the gate."""
        async with AsyncSessionLocal() as session:
            gate = GateDecision(
                decision_id="gd-r4",
                gate_id="gate-r4",
                project_id=seeded_project.project_id,
                gate_type="2",
                status="pending",
            )
            session.add(gate)
            await session.commit()

        res = client.post(
            "/api/v1/gates/gd-r4/reject",
            json={"reason": "Requirements incomplete"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "rejected"
        assert data["reason"] == "Requirements incomplete"

    @pytest.mark.asyncio
    async def test_reject_gate_reason_too_short(self, seeded_project: Project) -> None:
        """Reject with short reason returns 400."""
        async with AsyncSessionLocal() as session:
            gate = GateDecision(
                decision_id="gd-r5",
                gate_id="gate-r5",
                project_id=seeded_project.project_id,
                gate_type="2",
                status="pending",
            )
            session.add(gate)
            await session.commit()

        res = client.post(
            "/api/v1/gates/gd-r5/reject",
            json={"reason": "No"},
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_retry_gate(self, seeded_project: Project) -> None:
        """POST /retry resets gate to pending."""
        async with AsyncSessionLocal() as session:
            gate = GateDecision(
                decision_id="gd-r6",
                gate_id="gate-r6",
                project_id=seeded_project.project_id,
                gate_type="3",
                status="rejected",
                decision_type="reject",
                decision_by="user-a",
                reason="Issues",
            )
            session.add(gate)
            await session.commit()

        res = client.post("/api/v1/gates/gd-r6/retry")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "pending"
