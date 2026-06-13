"""Tests for Skill Pydantic schemas.

Covers skill and DAG DTO validation and serialization.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.skill import (
    DAGChangeLogDTO,
    DAGEdgeDTO,
    DAGNodeDTO,
    DAGSnapshotDTO,
    SkillResponseDTO,
    SkillScanRequestDTO,
    SkillScanResultItemDTO,
)


class TestSkillResponseDTO:
    """SkillResponseDTO tests."""

    def test_tags_from_json_string(self) -> None:
        """TEST-1401: tags parsed from JSON string.

        Covers field_validator for JSON text deserialization.
        """
        dto = SkillResponseDTO(
            skill_name="test",
            version="1.0.0",
            pattern="generator",
            directory_path="/tmp",
            tags='["sdlc", "planning"]',
        )
        assert dto.tags == ["sdlc", "planning"]

    def test_platforms_from_list(self) -> None:
        """TEST-1402: platforms accepted as list."""
        dto = SkillResponseDTO(
            skill_name="test",
            version="1.0.0",
            pattern="generator",
            directory_path="/tmp",
            platforms=["kimi", "claude"],
        )
        assert dto.platforms == ["kimi", "claude"]

    def test_tags_none(self) -> None:
        """TEST-1403: tags defaults to None when not provided."""
        dto = SkillResponseDTO(
            skill_name="test",
            version="1.0.0",
            pattern="generator",
            directory_path="/tmp",
        )
        assert dto.tags is None

    def test_tags_invalid_json_raises(self) -> None:
        """TEST-1404: Invalid JSON string for tags raises ValidationError.

        Covers edge case: malformed JSON propagated as validation error.
        """
        with pytest.raises(ValidationError):
            SkillResponseDTO(
                skill_name="test",
                version="1.0.0",
                pattern="generator",
                directory_path="/tmp",
                tags="not-json",
            )

    def test_tags_invalid_type(self) -> None:
        """TEST-1405: Invalid type for tags returns None."""
        dto = SkillResponseDTO(
            skill_name="test",
            version="1.0.0",
            pattern="generator",
            directory_path="/tmp",
            tags=123,
        )
        assert dto.tags is None

    def test_serialization(self) -> None:
        """TEST-1406: DTO serializes correctly."""
        dto = SkillResponseDTO(
            skill_id="skill-1",
            skill_name="brainstorming",
            version="1.0.0",
            pattern="generator",
            tags=["sdlc"],
            platforms=["kimi"],
            description="Trigger on ideas",
            directory_path="/skills",
            parse_status="PARSED",
        )
        d = dto.model_dump()
        assert d["skill_name"] == "brainstorming"
        assert d["tags"] == ["sdlc"]


class TestDAGNodeDTO:
    """DAGNodeDTO tests."""

    def test_defaults(self) -> None:
        """TEST-1407: position defaults to 0.0."""
        dto = DAGNodeDTO(node_id="n1", skill_id="s1")
        assert dto.position_x == 0.0
        assert dto.position_y == 0.0


class TestDAGEdgeDTO:
    """DAGEdgeDTO tests."""

    def test_defaults(self) -> None:
        """TEST-1408: confidence defaults to 100, is_auto_parsed to False."""
        dto = DAGEdgeDTO(
            edge_id="e1", source_node_id="n1", target_node_id="n2"
        )
        assert dto.confidence == 100
        assert dto.is_auto_parsed is False


class TestDAGSnapshotDTO:
    """DAGSnapshotDTO tests."""

    def test_empty_snapshot(self) -> None:
        """TEST-1409: Empty snapshot serializes correctly."""
        dto = DAGSnapshotDTO(nodes=[], edges=[])
        d = dto.model_dump()
        assert d["nodes"] == []
        assert d["edges"] == []


class TestSkillScanRequestDTO:
    """SkillScanRequestDTO tests."""

    def test_directory_path(self) -> None:
        """TEST-1410: Scan request accepts directory path."""
        dto = SkillScanRequestDTO(directory_path="/home/user/skills")
        assert dto.directory_path == "/home/user/skills"

    def test_directory_path_max_length(self) -> None:
        """TEST-1411: Directory path exceeds max length fails validation.

        Covers AC-S-001: Path length constraint.
        """
        with pytest.raises(ValidationError):
            SkillScanRequestDTO(directory_path="x" * 5000)


class TestSkillScanResultItemDTO:
    """SkillScanResultItemDTO tests."""

    def test_parse_status_default(self) -> None:
        """TEST-1412: Default parse_status is PARSED."""
        dto = SkillScanResultItemDTO(
            skill_name="test",
            version="1.0.0",
            pattern="generator",
            tags=["t1"],
            platforms=["kimi"],
            description="desc",
            directory_path="/tmp",
        )
        assert dto.parse_status == "PARSED"
        assert dto.parse_error_reason is None


class TestDAGChangeLogDTO:
    """DAGChangeLogDTO tests."""

    def test_optional_snapshots(self) -> None:
        """TEST-1413: before_snapshot and after_snapshot are optional."""
        dto = DAGChangeLogDTO(
            log_id="log-1",
            session_id="sess-1",
            operation_type="ADD_NODE",
            target_id="node-1",
        )
        assert dto.before_snapshot is None
        assert dto.after_snapshot is None
