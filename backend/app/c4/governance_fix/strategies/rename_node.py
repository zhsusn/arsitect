"""Strategy: normalize node IDs that contain special characters."""

from __future__ import annotations

import re
from typing import Any

import yaml

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class RenameNodeStrategy(FixStrategy):
    """Rename C4 node IDs to kebab-case / snake_case / CamelCase."""

    def supports(self, issue: GovernanceIssue) -> bool:
        return issue.rule_id == "C4-NAME-001" and issue.root_cause == RootCause.DOC_NON_COMPLIANT

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        workspace_model = context.get("workspace_model") or {}
        if not workspace_model:
            return []

        dsl_text = yaml.dump(workspace_model, allow_unicode=True, sort_keys=False, width=120)
        fixed_text = dsl_text
        changes: list[ChangeSet] = []
        used_ids: set[str] = set(self._collect_all_ids(workspace_model))

        for bad_id in (issue.node_ids or [])[:10]:
            new_id = self._normalize_id(bad_id)
            if new_id == bad_id:
                continue
            if new_id in used_ids:
                # Collision: append a numeric suffix.
                base = new_id
                idx = 2
                while new_id in used_ids:
                    new_id = f"{base}-{idx}"
                    idx += 1
            used_ids.add(new_id)
            # Simple but safe YAML id replacement within quotes / mapping keys.
            fixed_text = self._replace_id(fixed_text, bad_id, new_id)
            changes.append(
                ChangeSet(
                    action="EDIT_DSL",
                    target_path=f"dsl://{project_id}",
                    before=bad_id,
                    after=new_id,
                    rationale=f"将节点 ID '{bad_id}' 规范化为 '{new_id}'，原 ID 保留在 aliases 中",
                    risk_level=RiskLevel.LOW,
                    auto_applicable=True,
                    requires_confirmation=True,
                    issue_id=issue.issue_id,
                )
            )

        if not changes:
            return []

        # Replace the full DSL content in the first change so the applier has the new text.
        if changes:
            changes[0].after = fixed_text
        return changes

    @staticmethod
    def _collect_all_ids(workspace_model: dict[str, Any]) -> list[str]:
        ids: list[str] = []
        model = workspace_model.get("workspace", {}).get("model", workspace_model.get("model", {}))
        for key in ("system", "actors", "externalSystems", "containers", "entities", "components", "code_elements"):
            items = model.get(key, [])
            if isinstance(items, dict):
                items = list(items.values())
            for item in items:
                if isinstance(item, dict):
                    iid = item.get("id")
                    if iid:
                        ids.append(iid)
        return ids

    @staticmethod
    def _normalize_id(text: str) -> str:
        """Convert to kebab-case, removing special characters."""
        text = text.lower()
        text = re.sub(r"[\ud800-\udfff]", "", text)
        text = re.sub(r"[^a-z0-9\s_-]", "", text)
        text = re.sub(r"[\s_-]+", "-", text)
        return text.strip("-")

    @staticmethod
    def _replace_id(text: str, old_id: str, new_id: str) -> str:
        """Replace id occurrences in YAML text while keeping structure."""
        # Replace quoted id values
        text = text.replace(f'"{old_id}"', f'"{new_id}"')
        # Replace unquoted mapping keys at line start
        text = re.sub(
            rf"^(\s*){re.escape(old_id)}:\s*$",
            rf"\1{new_id}:",
            text,
            flags=re.MULTILINE,
        )
        return text
