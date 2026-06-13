"""State machine manager for Skill / Project / Artifact lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectState


# ============================================================
# Skill 级状态机（9 状态）
# ============================================================
class SkillState(StrEnum):
    """Skill execution states."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    GATE_WAITING = "gate_waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"


SKILL_TRANSITIONS: dict[SkillState, set[SkillState]] = {
    SkillState.PENDING: {SkillState.SCHEDULED},
    SkillState.SCHEDULED: {SkillState.EXECUTING, SkillState.SKIPPED},
    SkillState.EXECUTING: {
        SkillState.COMPLETED,
        SkillState.FAILED,
        SkillState.GATE_WAITING,
        SkillState.REVIEW_PENDING,
    },
    SkillState.GATE_WAITING: {
        SkillState.EXECUTING,
        SkillState.SKIPPED,
        SkillState.FAILED,
    },
    SkillState.REVIEW_PENDING: {SkillState.APPROVED, SkillState.EXECUTING},
    SkillState.APPROVED: {SkillState.COMPLETED},
    SkillState.FAILED: {SkillState.SCHEDULED},
    SkillState.SKIPPED: set(),
    SkillState.COMPLETED: set(),
}


# ============================================================
# Project 级状态机（4 状态）
# ============================================================
PROJECT_TRANSITIONS: dict[ProjectState, set[ProjectState]] = {
    ProjectState.DRAFT: {ProjectState.ACTIVE, ProjectState.CANCELLED},
    ProjectState.ACTIVE: {ProjectState.ARCHIVED, ProjectState.CANCELLED},
    ProjectState.ARCHIVED: set(),
    ProjectState.CANCELLED: set(),
}


# ============================================================
# Artifact 级状态机（4 状态）
# ============================================================
class ArtifactState(StrEnum):
    """Artifact review states."""

    GENERATED = "generated"
    EDITED = "edited"
    REVIEWING = "reviewing"
    ACCEPTED = "accepted"


ARTIFACT_TRANSITIONS: dict[ArtifactState, set[ArtifactState]] = {
    ArtifactState.GENERATED: {
        ArtifactState.EDITED,
        ArtifactState.REVIEWING,
        ArtifactState.ACCEPTED,
    },
    ArtifactState.EDITED: {ArtifactState.REVIEWING, ArtifactState.GENERATED},
    ArtifactState.REVIEWING: {ArtifactState.ACCEPTED, ArtifactState.EDITED},
    ArtifactState.ACCEPTED: {ArtifactState.EDITED},
}


class InvalidTransitionError(ValueError):
    """Raised when a state transition is not allowed."""


@dataclass
class StateTransition:
    """Record of a state transition."""

    entity_type: str
    entity_id: str
    from_state: str
    to_state: str
    timestamp: datetime
    triggered_by: str | None = None


class StateMachineManager:
    """Manage three-level state machines with validation and persistence."""

    TRANSITION_MAPS: dict[str, dict[Any, set[Any]]] = {
        "skill": SKILL_TRANSITIONS,
        "project": PROJECT_TRANSITIONS,
        "artifact": ARTIFACT_TRANSITIONS,
    }

    # Map generic states to existing ORM status values.
    _SKILL_STATUS_MAP: dict[SkillState, str] = {
        SkillState.PENDING: "NOT_STARTED",
        SkillState.SCHEDULED: "NOT_STARTED",
        SkillState.EXECUTING: "RUNNING",
        SkillState.GATE_WAITING: "RUNNING",
        SkillState.COMPLETED: "SUCCESS",
        SkillState.FAILED: "FAILED",
        SkillState.SKIPPED: "STOPPED",
        SkillState.REVIEW_PENDING: "RUNNING",
        SkillState.APPROVED: "SUCCESS",
    }

    _PROJECT_STATUS_MAP: dict[ProjectState, str] = {
        ProjectState.DRAFT: "Draft",
        ProjectState.ACTIVE: "Active",
        ProjectState.ARCHIVED: "Archived",
        ProjectState.CANCELLED: "Cancelled",
    }

    def __init__(
        self,
        db: AsyncSession | None,
        event_bus: Any | None = None,
    ) -> None:
        """Initialize with an async DB session and optional event bus.

        Args:
            db: SQLAlchemy async session for persistence.
            event_bus: Optional event bus for broadcasting transitions.
        """
        self.db = db
        self.event_bus = event_bus
        # Artifact states are kept in memory because the current ArtifactFile
        # model does not have a dedicated review-status column. A future
        # migration can add persistence without changing this interface.
        self._artifact_states: dict[str, ArtifactState] = {}

    async def transition(
        self,
        entity_type: str,
        entity_id: str,
        from_state: Any,
        to_state: Any,
        triggered_by: str | None = None,
    ) -> bool:
        """Execute a state transition.

        Steps:
            1. Validate transition legality.
            2. Persist new state.
            3. Publish event if event bus is available.
        """
        transitions = self.TRANSITION_MAPS.get(entity_type)
        if transitions is None:
            raise ValueError(f"Unknown entity type: {entity_type}")

        allowed = transitions.get(from_state, set())
        if to_state not in allowed:
            raise InvalidTransitionError(
                f"Invalid transition: {from_state.value} -> {to_state.value} for {entity_type}"
            )

        await self._persist_state(entity_type, entity_id, to_state)

        transition_record = StateTransition(
            entity_type=entity_type,
            entity_id=entity_id,
            from_state=from_state.value,
            to_state=to_state.value,
            timestamp=datetime.now(UTC),
            triggered_by=triggered_by,
        )

        if self.event_bus is not None:
            await self._publish_transition(transition_record)

        return True

    async def get_state(self, entity_type: str, entity_id: str) -> str | None:
        """Return the current state value for an entity."""
        return await self._query_state(entity_type, entity_id)

    async def recover_after_crash(self, project_id: str) -> list[str]:
        """Reset EXECUTING/GATE_WAITING skills to PENDING after a crash."""

        crashed = await self._query_crashed_skills(project_id)
        for skill_id in crashed:
            await self._persist_state("skill", skill_id, SkillState.PENDING.value)
            if self.event_bus is not None:
                await self._publish_transition(
                    StateTransition(
                        entity_type="skill",
                        entity_id=skill_id,
                        from_state=SkillState.EXECUTING.value,
                        to_state=SkillState.PENDING.value,
                        timestamp=datetime.now(UTC),
                        triggered_by="crash_recovery",
                    )
                )
        return crashed

    # ============================================================
    # Persistence helpers
    # ============================================================
    async def _persist_state(self, entity_type: str, entity_id: str, state: Any) -> None:
        """Persist state to the underlying storage."""
        if entity_type == "skill":
            await self._persist_skill_state(entity_id, state)
        elif entity_type == "project":
            await self._persist_project_state(entity_id, state)
        elif entity_type == "artifact":
            self._artifact_states[entity_id] = state

    async def _persist_skill_state(self, skill_id: str, state: Any) -> None:
        """Persist skill state to SkillExecution.overall_status."""
        from app.models.skill_execution import SkillExecution

        if self.db is None:
            return

        status_value = self._SKILL_STATUS_MAP.get(state, state.value)
        await self.db.execute(
            update(SkillExecution)
            .where(SkillExecution.execution_id == skill_id)
            .values(overall_status=status_value)
        )
        await self.db.commit()

    async def _persist_project_state(self, project_id: str, state: Any) -> None:
        """Persist project state to Project.project_status."""
        from app.models.project import Project

        if self.db is None:
            return

        status_value = self._PROJECT_STATUS_MAP.get(state, state.value)
        await self.db.execute(
            update(Project)
            .where(Project.project_id == project_id)
            .values(project_status=status_value)
        )
        await self.db.commit()

    async def _query_state(self, entity_type: str, entity_id: str) -> str | None:
        """Query current state from storage."""
        if entity_type == "skill":
            return await self._query_skill_state(entity_id)
        if entity_type == "project":
            return await self._query_project_state(entity_id)
        if entity_type == "artifact":
            state = self._artifact_states.get(entity_id)
            return state.value if state else None
        return None

    async def _query_skill_state(self, skill_id: str) -> str | None:
        from app.models.skill_execution import SkillExecution

        if self.db is None:
            return None

        result = await self.db.execute(
            select(SkillExecution.overall_status).where(SkillExecution.execution_id == skill_id)
        )
        status = result.scalar_one_or_none()
        return self._reverse_skill_status(status) if status else None

    async def _query_project_state(self, project_id: str) -> str | None:
        from app.models.project import Project

        if self.db is None:
            return None

        result = await self.db.execute(
            select(Project.project_status).where(Project.project_id == project_id)
        )
        status = result.scalar_one_or_none()
        return status.lower() if status else None

    async def _query_crashed_skills(self, project_id: str) -> list[str]:
        from app.models.skill_execution import SkillExecution

        if self.db is None:
            return []

        result = await self.db.execute(
            select(SkillExecution.execution_id)
            .where(SkillExecution.project_id == project_id)
            .where(
                SkillExecution.overall_status.in_([self._SKILL_STATUS_MAP[SkillState.EXECUTING]])
            )
        )
        return [row[0] for row in result.all()]

    @staticmethod
    def _reverse_skill_status(status: str | None) -> str | None:
        """Map ORM status back to generic SkillState value."""
        reverse_map = {
            "NOT_STARTED": SkillState.PENDING.value,
            "RUNNING": SkillState.EXECUTING.value,
            "SUCCESS": SkillState.COMPLETED.value,
            "FAILED": SkillState.FAILED.value,
            "STOPPED": SkillState.SKIPPED.value,
            "UNKNOWN": None,
        }
        return reverse_map.get(status, status.lower() if status else None)

    async def _publish_transition(self, transition: StateTransition) -> None:
        """Publish a transition event to the event bus."""
        from app.common.event_bus import DomainEvent

        if hasattr(self.event_bus, "publish"):
            self.event_bus.publish(
                DomainEvent(
                    event_type=f"{transition.entity_type}.state_changed",
                    aggregate_id=transition.entity_id,
                    payload={
                        "entity_id": transition.entity_id,
                        "from": transition.from_state,
                        "to": transition.to_state,
                        "triggered_by": transition.triggered_by,
                    },
                    source="state_machine",
                )
            )
