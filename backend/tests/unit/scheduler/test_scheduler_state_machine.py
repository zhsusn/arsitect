"""Tests for StateMachineManager."""

from __future__ import annotations

import pytest

from app.scheduler.state_machine import (
    InvalidTransitionError,
    SkillState,
    StateMachineManager,
)


class TestStateMachine:
    """Unit tests for the three-level state machine."""

    def test_valid_transition(self) -> None:
        """PENDING -> SCHEDULED is allowed."""
        sm = StateMachineManager(None)
        transitions = sm.TRANSITION_MAPS["skill"]
        assert SkillState.SCHEDULED in transitions[SkillState.PENDING]

    def test_invalid_transition(self) -> None:
        """COMPLETED -> EXECUTING is not allowed."""
        sm = StateMachineManager(None)
        transitions = sm.TRANSITION_MAPS["skill"]
        assert SkillState.EXECUTING not in transitions.get(SkillState.COMPLETED, set())

    def test_all_skill_states_have_transitions(self) -> None:
        """Every SkillState has a transition entry."""
        sm = StateMachineManager(None)
        for state in SkillState:
            assert state in sm.TRANSITION_MAPS["skill"]

    @pytest.mark.asyncio
    async def test_transition_allows_legal_move(self) -> None:
        """Transition succeeds for a legal move."""
        sm = StateMachineManager(None)
        result = await sm.transition(
            "skill",
            "skill-1",
            SkillState.PENDING,
            SkillState.SCHEDULED,
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_transition_rejects_illegal_move(self) -> None:
        """Transition raises InvalidTransitionError for an illegal move."""
        sm = StateMachineManager(None)
        with pytest.raises(InvalidTransitionError):
            await sm.transition(
                "skill",
                "skill-1",
                SkillState.COMPLETED,
                SkillState.EXECUTING,
            )

    @pytest.mark.asyncio
    async def test_unknown_entity_type_raises(self) -> None:
        """Unknown entity type raises ValueError."""
        sm = StateMachineManager(None)
        with pytest.raises(ValueError, match="Unknown entity type"):
            await sm.transition(
                "unknown",
                "x",
                SkillState.PENDING,
                SkillState.SCHEDULED,
            )
