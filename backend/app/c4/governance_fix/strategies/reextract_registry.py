"""Strategy: re-run C4 registry extraction to capture missing relationships."""

from __future__ import annotations

from typing import Any

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class ReExtractRegistryStrategy(FixStrategy):
    """Re-extract C4 registry when relationships are missing."""

    def supports(self, issue: GovernanceIssue) -> bool:
        return issue.root_cause == RootCause.RELATIONSHIP_MISSING and issue.rule_id in (
            "C4-ORPHAN-001",
            "C4-DISCONN-001",
            "VAL-001",
        )

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        return [
            ChangeSet(
                action="RUN_REGISTRY_EXTRACT",
                target_path=f"openspec/changes/{project_id}/baseline/_c4-registry.yaml",
                before="",
                after="",
                rationale="C4 关系抽取可能遗漏了最近的 import/调用，重新运行 registry 抽取",
                risk_level=RiskLevel.LOW,
                auto_applicable=True,
                requires_confirmation=False,
                issue_id=issue.issue_id,
            )
        ]
