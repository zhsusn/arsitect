"""Strategy: add missing C4 relationships to the DSL."""

from __future__ import annotations

from typing import Any

import yaml

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class AddRelationshipDocStrategy(FixStrategy):
    """Add a relationship edge to the DSL when code references an unmapped dependency."""

    def supports(self, issue: GovernanceIssue) -> bool:
        return issue.rule_id in ("IMP-C2F-001", "IMP-F2C-001") and issue.root_cause in (
            RootCause.DSL_MISSING_RELATIONSHIP,
            RootCause.RELATIONSHIP_MISSING,
        )

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        workspace_model = context.get("workspace_model") or {}
        node_ids = issue.node_ids or []
        if len(node_ids) < 2:
            return []
        source, target = node_ids[0], node_ids[1]

        new_model = self._add_relationship(workspace_model, source, target)
        if new_model is None:
            return []

        return [
            ChangeSet(
                action="EDIT_DSL",
                target_path=f"dsl://{project_id}",
                before=yaml.dump(workspace_model, allow_unicode=True, sort_keys=False, width=120),
                after=yaml.dump(new_model, allow_unicode=True, sort_keys=False, width=120),
                rationale=f"在 DSL 中补充代码已声明但未记录的依赖关系: '{source}' -> '{target}'",
                risk_level=RiskLevel.MEDIUM,
                auto_applicable=False,
                requires_confirmation=True,
                issue_id=issue.issue_id,
            )
        ]

    @staticmethod
    def _add_relationship(
        workspace_model: dict[str, Any],
        source: str,
        target: str,
    ) -> dict[str, Any] | None:
        import copy

        new_model = copy.deepcopy(workspace_model)
        model = new_model.get("workspace", {}).get("model", new_model.get("model", {}))
        relationships = model.get("relationships", [])

        for rel in relationships:
            if rel.get("sourceId") == source and rel.get("destinationId") == target:
                return None

        model["relationships"] = relationships + [
            {
                "sourceId": source,
                "destinationId": target,
                "description": "auto-added dependency",
            }
        ]
        return new_model
