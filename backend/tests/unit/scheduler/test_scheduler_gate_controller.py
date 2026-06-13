"""Tests for GateController."""

from __future__ import annotations

import asyncio

import pytest

from app.scheduler.gate_controller import GateController, GateDecision
from app.scheduler.state_machine import StateMachineManager


class TestGateController:
    """Unit tests for gate approval flow."""

    @pytest.fixture
    def controller(self) -> GateController:
        """Return an in-memory GateController."""
        sm = StateMachineManager(None)
        return GateController(sm)

    @pytest.mark.asyncio
    async def test_create_and_approve_gate(self, controller: GateController) -> None:
        """Create a gate and approve it."""
        gate_id = await controller.create_gate(
            "skill-1",
            "proj-1",
            {
                "status": "success",
                "stdout": "",
                "stderr": "",
                "output_artifacts": ["a.md"],
            },
        )

        pending = controller.get_pending_gates("proj-1")
        assert len(pending) == 1
        assert pending[0].gate_id == gate_id

        await controller.approve(gate_id, "user-1", "Looks good")
        gate = controller.get_gate(gate_id)
        assert gate is not None
        assert gate.decision == GateDecision.APPROVED.value
        assert gate.decider == "user-1"

    @pytest.mark.asyncio
    async def test_wait_for_approval(self, controller: GateController) -> None:
        """Asynchronously wait for approval."""
        gate_id = await controller.create_gate("skill-2", "proj-1", {"status": "success"})

        async def delayed_approve() -> None:
            await asyncio.sleep(0.05)
            await controller.approve(gate_id, "user-1", "")

        asyncio.create_task(delayed_approve())

        result = await controller.wait_for_approval(gate_id, timeout=5.0)
        assert result["decision"] == "approved"

    @pytest.mark.asyncio
    async def test_wait_timeout(self, controller: GateController) -> None:
        """Waiting without a decision returns timeout."""
        gate_id = await controller.create_gate("skill-3", "proj-1", {"status": "success"})
        result = await controller.wait_for_approval(gate_id, timeout=0.05)
        assert result["decision"] == "timeout"

    @pytest.mark.asyncio
    async def test_reject_gate(self, controller: GateController) -> None:
        """Rejecting a gate records the decision."""
        gate_id = await controller.create_gate("skill-4", "proj-1", {"status": "success"})
        await controller.reject(gate_id, "user-2", "Requirements incomplete")
        gate = controller.get_gate(gate_id)
        assert gate is not None
        assert gate.decision == GateDecision.REJECTED.value
        assert gate.notes == "Requirements incomplete"

    @pytest.mark.asyncio
    async def test_retry_gate(self, controller: GateController) -> None:
        """Retrying a gate resets it."""
        gate_id = await controller.create_gate("skill-5", "proj-1", {"status": "success"})
        await controller.reject(gate_id, "user-2", "Issues found")
        await controller.retry(gate_id, "user-3", "Retry requested")
        gate = controller.get_gate(gate_id)
        assert gate is not None
        assert gate.decision == GateDecision.RETRY.value
