"""Skill execution state machine."""

from __future__ import annotations

from enum import StrEnum

from app.core.exceptions import ValidationError


class ExecutionStatus(StrEnum):
    """Execution status enum."""

    NOT_STARTED = "NOT_STARTED"
    PREPARING = "PREPARING"
    PREP_FAILED = "PREP_FAILED"
    PREP_COMPLETED = "PREP_COMPLETED"
    EXECUTING = "EXECUTING"
    EXEC_FAILED = "EXEC_FAILED"
    EXEC_COMPLETED = "EXEC_COMPLETED"
    POST_PROCESSING = "POST_PROCESSING"
    POST_FAILED = "POST_FAILED"
    COMPLETED = "COMPLETED"
    INTERRUPTED = "INTERRUPTED"


_TRANSITIONS: dict[ExecutionStatus, set[ExecutionStatus]] = {
    ExecutionStatus.NOT_STARTED: {
        ExecutionStatus.PREPARING,
    },
    ExecutionStatus.PREPARING: {
        ExecutionStatus.PREP_COMPLETED,
        ExecutionStatus.PREP_FAILED,
    },
    ExecutionStatus.PREP_COMPLETED: {
        ExecutionStatus.EXECUTING,
    },
    ExecutionStatus.PREP_FAILED: set(),
    ExecutionStatus.EXECUTING: {
        ExecutionStatus.EXEC_COMPLETED,
        ExecutionStatus.EXEC_FAILED,
        ExecutionStatus.INTERRUPTED,
    },
    ExecutionStatus.EXEC_COMPLETED: {
        ExecutionStatus.POST_PROCESSING,
    },
    ExecutionStatus.EXEC_FAILED: set(),
    ExecutionStatus.INTERRUPTED: {
        ExecutionStatus.POST_PROCESSING,
    },
    ExecutionStatus.POST_PROCESSING: {
        ExecutionStatus.COMPLETED,
        ExecutionStatus.POST_FAILED,
    },
    ExecutionStatus.POST_FAILED: set(),
    ExecutionStatus.COMPLETED: set(),
}


class SkillExecutionStateMachine:
    """State machine for skill execution lifecycle."""

    def __init__(self, initial: ExecutionStatus = ExecutionStatus.NOT_STARTED) -> None:
        """Initialize with an initial status."""
        self._status = initial

    @property
    def status(self) -> ExecutionStatus:
        """Current status."""
        return self._status

    def transition(self, new_status: ExecutionStatus) -> None:
        """Transition to a new status.

        Raises:
            ValidationError: If the transition is not allowed.
        """
        allowed = _TRANSITIONS.get(self._status, set())
        if new_status not in allowed:
            raise ValidationError(
                detail=(
                    f"Invalid transition from {self._status.value} "
                    f"to {new_status.value}"
                )
            )
        self._status = new_status

    def can_transition(self, new_status: ExecutionStatus) -> bool:
        """Check if transition is allowed without changing state."""
        allowed = _TRANSITIONS.get(self._status, set())
        return new_status in allowed
