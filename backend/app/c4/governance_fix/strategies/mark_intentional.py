"""Strategy: mark orphan nodes as intentional in the C4 registry."""

from __future__ import annotations

from typing import Any

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class MarkIntentionalStrategy(FixStrategy):
    """Mark disconnected primitive/helper nodes as intentional_orphan."""

    def supports(self, issue: GovernanceIssue) -> bool:
        return (
            issue.rule_id in ("C4-ORPHAN-001", "C4-ORPHAN-002", "ORPHAN-002")
            and issue.root_cause == RootCause.INTENTIONAL_DESIGN
        )

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        registry = context.get("registry") or {}
        components = registry.get("components", {})
        changes: list[ChangeSet] = []
        for nid in issue.node_ids or []:
            info = components.get(nid)
            if not info:
                continue
            if info.get("intentional_orphan"):
                continue
            changes.append(
                ChangeSet(
                    action="TOGGLE_INTENTIONAL_ORPHAN",
                    target_path=f"openspec/changes/{project_id}/baseline/_c4-registry.yaml",
                    before=str(info.get("intentional_orphan", False)),
                    after="true",
                    rationale=f"节点 '{nid}' 是跨领域 helper / UI primitive，无需关联关系，标记为 intentional orphan",
                    risk_level=RiskLevel.LOW,
                    auto_applicable=True,
                    requires_confirmation=False,
                    issue_id=issue.issue_id,
                )
            )
        return changes
