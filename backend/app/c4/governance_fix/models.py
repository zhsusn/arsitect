"""Governance auto-fix domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RootCause(StrEnum):
    """Root cause taxonomy for governance issues."""

    DOC_NON_COMPLIANT = "DOC_NON_COMPLIANT"
    DOC_INCOMPLETE = "DOC_INCOMPLETE"
    DOC_CODE_MISMATCH = "DOC_CODE_MISMATCH"
    CODE_MISSING = "CODE_MISSING"
    RELATIONSHIP_MISSING = "RELATIONSHIP_MISSING"
    DSL_MISSING_RELATIONSHIP = "DSL_MISSING_RELATIONSHIP"
    DSL_UNAUTHORIZED_RELATIONSHIP = "DSL_UNAUTHORIZED_RELATIONSHIP"
    CODE_UNDESIGNED_RELATIONSHIP = "CODE_UNDESIGNED_RELATIONSHIP"
    CODE_DEAD = "CODE_DEAD"
    DSL_DEPRECATED = "DSL_DEPRECATED"
    NAME_DRIFT = "NAME_DRIFT"
    INTENTIONAL_DESIGN = "INTENTIONAL_DESIGN"
    NEEDS_HUMAN_DECISION = "NEEDS_HUMAN_DECISION"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class RiskLevel(StrEnum):
    """Risk level for a single change."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class GovernanceIssue:
    """Unified issue representation across all validators."""

    issue_id: str
    source: str
    rule_id: str
    severity: str
    message: str
    node_ids: list[str] = field(default_factory=list)
    c4_node_id: str = ""
    code_entity_id: str = ""
    fix_hint: str = ""
    fix_action: str = ""
    root_cause: str = RootCause.UNKNOWN
    auto_fixable: bool = False
    confidence: str = "LOW"  # LOW / MEDIUM / HIGH
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeSet:
    """A single concrete change that can be previewed and applied."""

    action: str
    target_path: str
    before: str | None = None
    after: str | None = None
    rationale: str = ""
    risk_level: str = RiskLevel.LOW
    auto_applicable: bool = False
    requires_confirmation: bool = True
    issue_id: str = ""


@dataclass
class FixPlan:
    """Collection of changes proposed for a set of issues."""

    project_id: str
    issue_ids: list[str] = field(default_factory=list)
    changes: list[ChangeSet] = field(default_factory=list)
    dry_run: bool = True
    session_id: str = ""


@dataclass
class FixResult:
    """Result after applying a fix plan."""

    project_id: str
    session_id: str
    applied_changes: list[ChangeSet] = field(default_factory=list)
    skipped_changes: list[ChangeSet] = field(default_factory=list)
    new_analysis: dict[str, Any] = field(default_factory=dict)
    backup_dir: str = ""
