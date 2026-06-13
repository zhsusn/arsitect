"""Strategy: remove unauthorized or impossible C4 relationships."""

from __future__ import annotations

from typing import Any

import yaml

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class RemoveRelationshipStrategy(FixStrategy):
    """Remove a relationship edge from the DSL when it violates C4 security/coupling rules."""

    def supports(self, issue: GovernanceIssue) -> bool:
        return issue.rule_id in ("IMP-C2F-001", "IMP-F2C-001") and issue.root_cause in (
            RootCause.DSL_UNAUTHORIZED_RELATIONSHIP,
            RootCause.CODE_UNDESIGNED_RELATIONSHIP,
        )

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        workspace_model = context.get("workspace_model") or {}
        node_ids = issue.node_ids or []
        source = node_ids[0] if len(node_ids) > 0 else ""
        target = node_ids[1] if len(node_ids) > 1 else ""

        new_model = self._remove_relationship(workspace_model, source, target)
        if new_model is None:
            return []

        rationale = f"移除未授权/不可能的依赖关系: '{source}' -> '{target}'"
        return [
            ChangeSet(
                action="EDIT_DSL",
                target_path=f"dsl://{project_id}",
                before=yaml.dump(workspace_model, allow_unicode=True, sort_keys=False, width=120),
                after=yaml.dump(new_model, allow_unicode=True, sort_keys=False, width=120),
                rationale=rationale,
                risk_level=RiskLevel.HIGH,
                auto_applicable=False,
                requires_confirmation=True,
                issue_id=issue.issue_id,
            )
        ]

    @staticmethod
    def _remove_relationship(
        workspace_model: dict[str, Any],
        source: str | None,
        target: str | None,
    ) -> dict[str, Any] | None:
        if not source or not target:
            return None
        import copy

        new_model = copy.deepcopy(workspace_model)
        model = new_model.get("workspace", {}).get("model", new_model.get("model", {}))
        relationships = model.get("relationships", [])
        before = len(relationships)
        model["relationships"] = [
            r
            for r in relationships
            if not (r.get("sourceId") == source and r.get("destinationId") == target)
        ]
        if len(model["relationships"]) == before:
            return None
        return new_model
