"""Strategy: add missing component definitions or aliases to C4 DSL."""

from __future__ import annotations

from typing import Any

import yaml

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class AddComponentDocStrategy(FixStrategy):
    """Add a component to DSL when code exists but design is incomplete,
    or update aliases when naming differs."""

    def supports(self, issue: GovernanceIssue) -> bool:
        return issue.rule_id in ("CON-F2C-001", "CON-C2F-001") and issue.root_cause in (
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
        components = model.get("components", [])
        component_ids = {c.get("id", "") for c in components}
        containers = {c.get("id", "") for c in model.get("containers", [])}

        name = issue.c4_node_id or issue.code_entity_id or ""
        if not name:
            return []

        # Try to find matching code entity to infer container and type.
        code_entity = self._find_code_entity(name, context)
        container_id = ""
        if code_entity:
            container_id = code_entity.get("container_hint", "")
        if not container_id or container_id not in containers:
            container_id = (
                "backend-api" if "backend-api" in containers else next(iter(containers), "")
            )

        if issue.root_cause == RootCause.DOC_INCOMPLETE:
            if name in component_ids:
                return []
            new_component = {
                "id": name,
                "name": name.replace("-", " ").replace("_", " ").title(),
                "properties": {"container_id": container_id},
            }
            new_model = self._add_component(workspace_model, new_component)
            rationale = f"在 DSL 中补充代码已存在但未定义的组件 '{name}'"
        else:
            # DOC_CODE_MISMATCH: add alias to existing component.
            new_model = self._add_alias(workspace_model, name)
            rationale = f"为组件添加别名 '{name}' 以匹配代码实体"

        if new_model is None:
            return []

        return [
            ChangeSet(
                action="EDIT_DSL",
                target_path=f"dsl://{project_id}",
                before=yaml.dump(workspace_model, allow_unicode=True, sort_keys=False, width=120),
                after=yaml.dump(new_model, allow_unicode=True, sort_keys=False, width=120),
                rationale=rationale,
                risk_level=RiskLevel.MEDIUM,
                auto_applicable=False,
                requires_confirmation=True,
                issue_id=issue.issue_id,
            )
        ]

    @staticmethod
    def _find_code_entity(name: str, context: dict[str, Any]) -> dict[str, Any] | None:
        name_lower = name.lower().replace("-", "_")
        for e in context.get("code_entities", []):
            entity: dict[str, Any] = e
            e_name = entity.get("name", "").lower().replace("-", "_")
            if e_name == name_lower or name_lower in e_name or e_name in name_lower:
                return entity
        return None

    @staticmethod
    def _add_component(
        workspace_model: dict[str, Any], component: dict[str, Any]
    ) -> dict[str, Any] | None:
        import copy

        new_model: dict[str, Any] = copy.deepcopy(workspace_model)
        model = new_model.get("workspace", {}).get("model", new_model.get("model", {}))
        model.setdefault("components", []).append(component)
        return new_model

    @staticmethod
    def _add_alias(workspace_model: dict[str, Any], alias: str) -> dict[str, Any] | None:
        import copy

        new_model = copy.deepcopy(workspace_model)
        model = new_model.get("workspace", {}).get("model", new_model.get("model", {}))
        for comp in model.get("components", []):
            aliases = comp.get("aliases", [])
            if alias not in aliases:
                aliases.append(alias)
                comp["aliases"] = aliases
                return new_model
        return None
