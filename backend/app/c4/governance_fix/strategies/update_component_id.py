"""Strategy: rename C4 component ids to match code entities."""

from __future__ import annotations

from typing import Any

import yaml

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class UpdateComponentIdStrategy(FixStrategy):
    """Rename a DSL component id to match the corresponding code entity name,
    updating relationships and container references."""

    def supports(self, issue: GovernanceIssue) -> bool:
        return issue.rule_id in ("CON-F2C-001", "CON-C2F-001") and issue.root_cause in (
            RootCause.DOC_CODE_MISMATCH,
            RootCause.NAME_DRIFT,
        )

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        old_id = issue.c4_node_id
        new_id = issue.code_entity_id
        if not old_id or not new_id or old_id == new_id:
            return []

        workspace_model = context.get("workspace_model") or {}
        new_model = self._rename_component(workspace_model, old_id, new_id)
        if new_model is None:
            return []

        return [
            ChangeSet(
                action="EDIT_DSL",
                target_path=f"dsl://{project_id}",
                before=yaml.dump(workspace_model, allow_unicode=True, sort_keys=False, width=120),
                after=yaml.dump(new_model, allow_unicode=True, sort_keys=False, width=120),
                rationale=f"将 C4 组件标识从 '{old_id}' 重命名为代码实体 '{new_id}'，并同步更新关系引用",
                risk_level=RiskLevel.MEDIUM,
                auto_applicable=False,
                requires_confirmation=True,
                issue_id=issue.issue_id,
            )
        ]

    @staticmethod
    def _rename_component(
        workspace_model: dict[str, Any],
        old_id: str,
        new_id: str,
    ) -> dict[str, Any] | None:
        import copy

        new_model = copy.deepcopy(workspace_model)
        model = new_model.get("workspace", {}).get("model", new_model.get("model", {}))

        found = False
        for comp in model.get("components", []):
            if comp.get("id") == old_id:
                comp["id"] = new_id
                found = True
                break
        if not found:
            return None

        for rel in model.get("relationships", []):
            if rel.get("sourceId") == old_id:
                rel["sourceId"] = new_id
            if rel.get("destinationId") == old_id:
                rel["destinationId"] = new_id
        return new_model
