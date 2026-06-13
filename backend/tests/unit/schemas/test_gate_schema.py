"""Tests for Gate Pydantic schemas.

Covers gate decision DTO validation and serialization.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.gate import GateDecisionResponseDTO, GateRejectRequestDTO


class TestGateDecisionResponseDTO:
    """GateDecisionResponseDTO tests."""

    def _make_dto(self, **overrides) -> GateDecisionResponseDTO:
        defaults = {
            "decision_id": "gd-1",
            "gate_id": "gate-1",
            "project_id": "proj-1",
            "gate_type": "1",
            "status": "pending",
            "confidence": None,
            "decision_type": None,
            "decision_by": None,
            "decision_at": None,
            "duration_sec": None,
            "reason": None,
        }
        defaults.update(overrides)
        return GateDecisionResponseDTO(**defaults)

    def test_unlocked_stages_from_json_string(self) -> None:
        """TEST-1301: unlocked_stages parsed from JSON string.

        Covers field_validator for JSON deserialization.
        """
        dto = self._make_dto(unlocked_stages='["stage-1", "stage-2"]')
        assert dto.unlocked_stages == ["stage-1", "stage-2"]

    def test_unlocked_stages_from_list(self) -> None:
        """TEST-1302: unlocked_stages accepted as list."""
        dto = self._make_dto(unlocked_stages=["stage-3"])
        assert dto.unlocked_stages == ["stage-3"]

    def test_unlocked_stages_from_none(self) -> None:
        """TEST-1303: unlocked_stages defaults to empty list when None."""
        dto = self._make_dto(unlocked_stages=None)
        assert dto.unlocked_stages == []

    def test_unlocked_stages_from_invalid_string(self) -> None:
        """TEST-1304: unlocked_stages raises error on invalid JSON string.

        Covers edge case: malformed JSON string.
        """
        with pytest.raises((ValidationError, json.JSONDecodeError)):
            self._make_dto(unlocked_stages="not-json")

    def test_unlocked_stages_from_invalid_type(self) -> None:
        """TEST-1305: unlocked_stages defaults to empty list on invalid type."""
        dto = self._make_dto(unlocked_stages=123)
        assert dto.unlocked_stages == []

    def test_serialization(self) -> None:
        """TEST-1306: DTO serializes correctly."""
        now = datetime.now(UTC)
        dto = self._make_dto(
            decision_id="gd-6",
            gate_id="gate-6",
            project_id="proj-6",
            gate_type="1",
            status="passed",
            confidence="high",
            decision_type="auto",
            decision_by="user-1",
            decision_at=now,
            duration_sec=30,
            reason="Approved",
            unlocked_stages=["stage-1"],
        )
        d = dto.model_dump()
        assert d["decision_id"] == "gd-6"
        assert d["status"] == "passed"
        assert d["unlocked_stages"] == ["stage-1"]


class TestGateRejectRequestDTO:
    """GateRejectRequestDTO tests."""

    def test_reject_reason(self) -> None:
        """TEST-1307: Reject DTO requires reason."""
        dto = GateRejectRequestDTO(reason="Insufficient documentation")
        assert dto.reason == "Insufficient documentation"
