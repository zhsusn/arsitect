"""Gate controller for human-in-the-loop approval."""

from __future__ import annotations

import asyncio
import contextlib
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.gate_repo import GateRepository
from app.models.gate_decision import GateDecision as GateDecisionModel
from app.scheduler.state_machine import InvalidTransitionError, SkillState


class GateDecision(StrEnum):
    """Gate resolution decisions."""

    APPROVED = "approved"
    REJECTED = "rejected"
    RETRY = "retry"
    BYPASSED = "bypassed"


@dataclass
class GateItem:
    """In-memory pending gate item."""

    gate_id: str
    skill_id: str
    project_id: str
    summary: str
    created_at: datetime
    decision: str | None = None
    decider: str | None = None
    notes: str | None = None
    resolved_at: datetime | None = None


class GateController:
    """Manage pending gate queue, self-check summaries and audit logging."""

    def __init__(
        self,
        state_machine: Any,
        event_bus: Any | None = None,
        db: AsyncSession | None = None,
    ) -> None:
        """Initialize with state machine and optional event bus / DB session.

        Args:
            state_machine: State machine manager for skill state transitions.
            event_bus: Optional event bus for broadcasting gate events.
            db: Optional async session for persisting GateDecision records.
        """
        self.state_machine = state_machine
        self.event_bus = event_bus
        self.db = db
        self._pending_gates: dict[str, GateItem] = {}
        self._wait_events: dict[str, asyncio.Event] = {}

    async def create_gate(
        self,
        skill_id: str,
        project_id: str,
        exec_result: dict[str, Any],
        gate_type: str = "2",
    ) -> str:
        """Create a pending gate.

        Flow:
            1. Generate AI self-check summary.
            2. Persist GateDecision record.
            3. Move skill state to GATE_WAITING.
            4. Broadcast gate.created event.
        """
        gate_id = f"gate-{skill_id}-{int(datetime.now(UTC).timestamp())}"
        summary = await self._generate_summary(skill_id, exec_result)

        gate_item = GateItem(
            gate_id=gate_id,
            skill_id=skill_id,
            project_id=project_id,
            summary=summary,
            created_at=datetime.now(UTC),
        )
        self._pending_gates[gate_id] = gate_item
        self._wait_events[gate_id] = asyncio.Event()

        if self.db is not None:
            repo = GateRepository(self.db)
            await repo.create(
                GateDecisionModel(
                    decision_id=gate_id,
                    gate_id=gate_id,
                    project_id=project_id,
                    gate_type=gate_type,
                    status="pending",
                )
            )

        with contextlib.suppress(InvalidTransitionError):
            await self.state_machine.transition(
                entity_type="skill",
                entity_id=skill_id,
                from_state=SkillState.EXECUTING,
                to_state=SkillState.GATE_WAITING,
            )

        await self._publish(
            "gate.created",
            {
                "gate_id": gate_id,
                "skill_id": skill_id,
                "project_id": project_id,
                "summary": summary,
            },
        )

        return gate_id

    async def wait_for_approval(self, gate_id: str, timeout: float | None = None) -> dict[str, Any]:
        """Asynchronously wait for a gate decision."""
        event = self._wait_events.get(gate_id)
        if event is None:
            return {"decision": "error", "notes": "Gate not found"}

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except TimeoutError:
            return {"decision": "timeout", "notes": "Approval timed out"}

        gate = self._pending_gates.get(gate_id)
        if gate is None or gate.decision is None:
            return {"decision": "error", "notes": "No decision recorded"}

        return {
            "decision": gate.decision,
            "notes": gate.notes or "",
            "decider": gate.decider or "",
        }

    async def approve(self, gate_id: str, user_id: str, notes: str = "") -> bool:
        """Approve a gate."""
        return await self._resolve(gate_id, GateDecision.APPROVED, user_id, notes)

    async def reject(self, gate_id: str, user_id: str, reason: str = "") -> bool:
        """Reject a gate."""
        return await self._resolve(gate_id, GateDecision.REJECTED, user_id, reason)

    async def retry(self, gate_id: str, user_id: str, notes: str = "") -> bool:
        """Retry a gate (reset skill to scheduled)."""
        return await self._resolve(gate_id, GateDecision.RETRY, user_id, notes)

    async def bypass(self, gate_id: str, admin_id: str, reason: str = "") -> bool:
        """Bypass a gate (admin privilege required by caller)."""
        return await self._resolve(gate_id, GateDecision.BYPASSED, admin_id, reason)

    async def _load_gate_from_db(self, gate_id: str) -> GateItem | None:
        """Load a gate from the ORM into memory if it exists.

        Any persisted gate can be resolved, including already-rejected gates
        that are being retried.
        """
        if self.db is None:
            return None

        repo = GateRepository(self.db)
        record = await repo.get_by_id(gate_id)
        if record is None:
            return None

        gate = GateItem(
            gate_id=record.decision_id,
            skill_id=record.gate_id,
            project_id=record.project_id,
            summary="",
            created_at=record.created_at or datetime.now(UTC),
        )
        self._pending_gates[gate_id] = gate
        self._wait_events[gate_id] = asyncio.Event()
        return gate

    async def _resolve(
        self,
        gate_id: str,
        decision: GateDecision,
        user_id: str,
        notes: str,
    ) -> bool:
        """Process a gate decision."""
        gate = self._pending_gates.get(gate_id)
        if gate is None:
            gate = await self._load_gate_from_db(gate_id)
        if gate is None:
            return False

        gate.decision = decision.value
        gate.decider = user_id
        gate.notes = notes
        gate.resolved_at = datetime.now(UTC)

        self._write_audit_log(gate)

        # Update state machine
        if decision == GateDecision.APPROVED:
            await self._transition_skill(
                gate.skill_id,
                SkillState.GATE_WAITING,
                SkillState.EXECUTING,
                user_id,
            )
        elif decision == GateDecision.REJECTED:
            await self._transition_skill(
                gate.skill_id,
                SkillState.GATE_WAITING,
                SkillState.FAILED,
                user_id,
            )
        elif decision == GateDecision.RETRY:
            await self._transition_skill(
                gate.skill_id,
                SkillState.GATE_WAITING,
                SkillState.SCHEDULED,
                user_id,
            )
        elif decision == GateDecision.BYPASSED:
            await self._transition_skill(
                gate.skill_id,
                SkillState.GATE_WAITING,
                SkillState.EXECUTING,
                user_id,
            )

        # Persist decision in ORM (map generic decisions to existing schema).
        if self.db is not None:
            repo = GateRepository(self.db)
            record = await repo.get_by_id(gate_id)
            if record is not None:
                now = datetime.now(UTC)
                record.status = self._decision_to_db_status(decision)
                record.decision_type = decision.value
                record.decision_by = user_id
                record.decision_at = now
                record.reason = notes or None
                created_at = record.created_at
                if created_at is not None:
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=UTC)
                    record.duration_sec = int((now - created_at).total_seconds())
                await repo.update(record)

        event = self._wait_events.get(gate_id)
        if event is not None:
            event.set()

        await self._publish(
            "gate.resolved",
            {
                "gate_id": gate_id,
                "decision": decision.value,
                "skill_id": gate.skill_id,
                "project_id": gate.project_id,
                "decider": user_id,
            },
        )

        return True

    async def _transition_skill(
        self,
        skill_id: str,
        from_state: SkillState,
        to_state: SkillState,
        user_id: str,
    ) -> None:
        """Transition skill state, ignoring invalid transitions gracefully."""
        with contextlib.suppress(InvalidTransitionError):
            await self.state_machine.transition(
                entity_type="skill",
                entity_id=skill_id,
                from_state=from_state,
                to_state=to_state,
                triggered_by=user_id,
            )

    @staticmethod
    def _decision_to_db_status(decision: GateDecision) -> str:
        """Map generic gate decision to GateDecision ORM status value."""
        mapping = {
            GateDecision.APPROVED: "passed",
            GateDecision.REJECTED: "rejected",
            GateDecision.RETRY: "pending",
            GateDecision.BYPASSED: "bypassed",
        }
        return mapping[decision]

    def get_pending_gates(self, project_id: str | None = None) -> list[GateItem]:
        """Return pending gates, optionally filtered by project."""
        gates = self._pending_gates.values()
        if project_id is not None:
            gates = [g for g in gates if g.project_id == project_id]
        return [g for g in gates if g.decision is None]

    def get_gate(self, gate_id: str) -> GateItem | None:
        """Return a single gate item."""
        return self._pending_gates.get(gate_id)

    async def _generate_summary(self, skill_id: str, exec_result: dict[str, Any]) -> str:
        """Generate a self-check summary for the gate."""
        stdout = exec_result.get("stdout", "")[:500]
        stderr = exec_result.get("stderr", "")[:500]
        artifacts = exec_result.get("output_artifacts", [])

        return f"""Skill: {skill_id}
Status: {exec_result.get("status", "unknown")}
Duration: {exec_result.get("duration_ms", 0)}ms
Exit Code: {exec_result.get("exit_code", "N/A")}
Output Artifacts: {", ".join(artifacts) if artifacts else "None"}
Stderr Preview: {stderr[:200]}
Stdout Preview: {stdout[:200]}
"""

    def _write_audit_log(self, gate: GateItem) -> None:
        """Append decision to human-decisions.md under the project directory."""
        log_path = os.path.join("./projects", gate.project_id, "human-decisions.md")
        entry = f"""
## {gate.resolved_at.isoformat() if gate.resolved_at else datetime.now(UTC).isoformat()} - {gate.decision.upper() if gate.decision else "UNKNOWN"}
- Gate: {gate.gate_id}
- Skill: {gate.skill_id}
- Decider: {gate.decider}
- Notes: {gate.notes or "N/A"}

"""
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)

    async def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish an event to the event bus."""
        from app.common.event_bus import DomainEvent

        if self.event_bus is None or not hasattr(self.event_bus, "publish"):
            return

        self.event_bus.publish(
            DomainEvent(
                event_type=event_type,
                aggregate_id=payload.get("project_id", ""),
                payload=payload,
                source="gate_controller",
            )
        )
