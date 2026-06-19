"""Project stage runtime state machine.

负责校验并执行 project_stage.runtime_status 的状态转换，
同时维护 started_at / completed_at 时间戳。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from app.core.exceptions import ConflictError
from app.models.project_stage import ProjectStage


class StageRuntimeStatus:
    """Runtime status constants for project stages."""

    NOT_STARTED = "not_started"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW_PENDING = "review_pending"
    GATE_PENDING = "gate_pending"
    PASSED = "passed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class StageStateMachine:
    """Finite state machine for stage runtime status transitions."""

    TERMINAL_STATUSES: ClassVar[set[str]] = {
        StageRuntimeStatus.PASSED,
        StageRuntimeStatus.SKIPPED,
    }

    _TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        StageRuntimeStatus.NOT_STARTED: {
            StageRuntimeStatus.READY,
            StageRuntimeStatus.SKIPPED,
        },
        StageRuntimeStatus.READY: {
            StageRuntimeStatus.IN_PROGRESS,
            StageRuntimeStatus.SKIPPED,
        },
        StageRuntimeStatus.IN_PROGRESS: {
            StageRuntimeStatus.REVIEW_PENDING,
            StageRuntimeStatus.BLOCKED,
        },
        StageRuntimeStatus.REVIEW_PENDING: {
            StageRuntimeStatus.GATE_PENDING,
            StageRuntimeStatus.PASSED,
        },
        StageRuntimeStatus.GATE_PENDING: {
            StageRuntimeStatus.PASSED,
            StageRuntimeStatus.BLOCKED,
        },
        StageRuntimeStatus.BLOCKED: {
            StageRuntimeStatus.IN_PROGRESS,
            StageRuntimeStatus.READY,
        },
        StageRuntimeStatus.PASSED: {
            StageRuntimeStatus.NOT_STARTED,
        },
        StageRuntimeStatus.SKIPPED: set(),
    }

    @classmethod
    def validate_transition(cls, current: str, target: str) -> None:
        """Validate that a transition is allowed.

        Args:
            current: Current runtime status.
            target: Target runtime status.

        Raises:
            ConflictError: If the transition is not allowed.
        """
        allowed = cls._TRANSITIONS.get(current, set())
        if target not in allowed:
            raise ConflictError(
                detail=f"Invalid stage transition from '{current}' to '{target}'"
            )

    @classmethod
    def transition(
        cls,
        stage: ProjectStage,
        target_status: str,
        *,
        set_started: bool = True,
        set_completed: bool = False,
    ) -> None:
        """Apply a runtime status transition to a stage object.

        Args:
            stage: ProjectStage instance.
            target_status: Target runtime status.
            set_started: Whether to set started_at when entering IN_PROGRESS.
            set_completed: Whether to set completed_at when entering PASSED/SKIPPED.
        """
        current = stage.runtime_status
        cls.validate_transition(current, target_status)
        stage.runtime_status = target_status

        now = datetime.now(UTC)
        if set_started and target_status == StageRuntimeStatus.IN_PROGRESS:
            stage.started_at = now
        if set_completed and target_status in cls.TERMINAL_STATUSES:
            stage.completed_at = now

    @classmethod
    def is_terminal(cls, status: str) -> bool:
        """Return True if the status is terminal."""
        return status in cls.TERMINAL_STATUSES
