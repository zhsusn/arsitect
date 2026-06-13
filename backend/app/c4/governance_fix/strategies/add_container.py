"""Strategy: add missing L2 containers to the C4 DSL."""

from __future__ import annotations

from typing import Any

import yaml

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class AddContainerStrategy(FixStrategy):
    """Add a container definition inferred from code directory or issue context."""

    def supports(self, issue: GovernanceIssue) -> bool:
        return issue.rule_id in ("CON-M2C-001", "VAL-003", "VAL-004") and issue.root_cause in (
            RootCause.DOC_INCOMPLETE,
            RootCause.DOC_CODE_MISMATCH,
        )

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        workspace_model = context.get("workspace_model") or {}
        model = workspace_model.get("workspace", {}).get("model", workspace_model.get("model", {}))
        containers = model.get("containers", [])
        existing_ids = {c.get("id", "") for c in containers}

        container_id = issue.c4_node_id or issue.code_entity_id or ""
        if not container_id or container_id in existing_ids:
            return []

        # Normalize and produce a human-readable name.
        name = container_id.replace("-", " ").replace("_", " ").title()
        new_container = {
            "id": container_id,
            "name": name,
            "technology": "TBD",
        }

        new_model = self._patch_model(workspace_model, new_container)
        new_dsl = yaml.dump(new_model, allow_unicode=True, sort_keys=False, width=120)

        return [
            ChangeSet(
                action="EDIT_DSL",
                target_path=f"dsl://{project_id}",
                before=yaml.dump(workspace_model, allow_unicode=True, sort_keys=False, width=120),
                after=new_dsl,
                rationale=f"在 DSL 中补充缺失的 L2 容器 '{container_id}'",
                risk_level=RiskLevel.MEDIUM,
                auto_applicable=False,
                requires_confirmation=True,
                issue_id=issue.issue_id,
            )
        ]

    @staticmethod
    def _patch_model(workspace_model: dict[str, Any], container: dict[str, str]) -> dict[str, Any]:
        import copy

        new_model = copy.deepcopy(workspace_model)
        model = new_model.get("workspace", {}).get("model", new_model.get("model", {}))
        model.setdefault("containers", []).append(container)
        return new_model
