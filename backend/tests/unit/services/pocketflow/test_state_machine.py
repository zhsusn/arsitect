"""Tests for SkillExecutionStateMachine."""

from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.services.pocketflow.state_machine import ExecutionStatus, SkillExecutionStateMachine


class TestSkillExecutionStateMachine:
    """State machine tests."""

    def test_initial_status(self) -> None:
        """Default status is NOT_STARTED."""
        sm = SkillExecutionStateMachine()
        assert sm.status == ExecutionStatus.NOT_STARTED

    def test_valid_prep_transition(self) -> None:
        """NOT_STARTED -> PREPARING is valid."""
        sm = SkillExecutionStateMachine()
        sm.transition(ExecutionStatus.PREPARING)
        assert sm.status == ExecutionStatus.PREPARING

    def test_invalid_prep_to_exec(self) -> None:
        """NOT_STARTED -> EXECUTING is invalid."""
        sm = SkillExecutionStateMachine()
        with pytest.raises(ValidationError):
            sm.transition(ExecutionStatus.EXECUTING)

    def test_full_pipeline_transitions(self) -> None:
        """Full valid pipeline: NOT_STARTED -> PREPARING -> PREP_COMPLETED -> EXECUTING -> EXEC_COMPLETED -> POST_PROCESSING -> COMPLETED."""
        sm = SkillExecutionStateMachine()
        sm.transition(ExecutionStatus.PREPARING)
        sm.transition(ExecutionStatus.PREP_COMPLETED)
        sm.transition(ExecutionStatus.EXECUTING)
        sm.transition(ExecutionStatus.EXEC_COMPLETED)
        sm.transition(ExecutionStatus.POST_PROCESSING)
        sm.transition(ExecutionStatus.COMPLETED)
        assert sm.status == ExecutionStatus.COMPLETED

    def test_exec_interrupted(self) -> None:
        """EXECUTING -> INTERRUPTED is valid."""
        sm = SkillExecutionStateMachine(ExecutionStatus.EXECUTING)
        sm.transition(ExecutionStatus.INTERRUPTED)
        assert sm.status == ExecutionStatus.INTERRUPTED

    def test_can_transition(self) -> None:
        """can_transition checks without changing state."""
        sm = SkillExecutionStateMachine(ExecutionStatus.PREP_COMPLETED)
        assert sm.can_transition(ExecutionStatus.EXECUTING) is True
        assert sm.can_transition(ExecutionStatus.COMPLETED) is False
        assert sm.status == ExecutionStatus.PREP_COMPLETED

    def test_prep_failed_terminal(self) -> None:
        """PREP_FAILED has no outgoing transitions."""
        sm = SkillExecutionStateMachine(ExecutionStatus.PREP_FAILED)
        assert sm.can_transition(ExecutionStatus.EXECUTING) is False
        with pytest.raises(ValidationError):
            sm.transition(ExecutionStatus.EXECUTING)

    def test_exec_failed_terminal(self) -> None:
        """EXEC_FAILED has no outgoing transitions."""
        sm = SkillExecutionStateMachine(ExecutionStatus.EXEC_FAILED)
        assert sm.can_transition(ExecutionStatus.POST_PROCESSING) is False
        with pytest.raises(ValidationError):
            sm.transition(ExecutionStatus.POST_PROCESSING)
