"""Extraction result schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class C4Snippet:
    """Extracted C4 structured snippet."""

    element_type: str
    element_id: str
    name: str = ""
    description: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    source_location: str = ""
    confidence: float = 1.0


@dataclass
class LintIssue:
    """Lint diagnosis issue."""

    rule_id: str
    severity: str  # BLOCKER | ERROR | WARNING | INFO
    message: str
    location: str
    fix_hint: str
    auto_fixable: bool
    fix_strategy: str  # AUTO | SEMI_AUTO | MANUAL


@dataclass
class LintReport:
    """Lint diagnosis report."""

    file_path: str
    doc_type: str | None
    passed: bool
    issues: list[LintIssue] = field(default_factory=list)
    fixed_content: str | None = None
    summary: str = ""
