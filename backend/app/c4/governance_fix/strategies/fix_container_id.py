"""Strategy: fix component container_id references."""

from __future__ import annotations

from typing import Any

import yaml

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class FixContainerIdStrategy(FixStrategy):
    """Correct container_id on components using registry or code-path hints."""

    def supports(self, issue: GovernanceIssue) -> bool:
        return issue.rule_id in ("C4-LEVEL-001", "VAL-003", "VAL-004") and issue.root_cause in (
            RootCause.DOC_NON_COMPLIANT,
            RootCause.DOC_CODE_MISMATCH,
        )

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        workspace_model = context.get("workspace_model") or {}
        registry = context.get("registry") or {}
        registry_components = registry.get("components", {})
        model = workspace_model.get("workspace", {}).get("model", workspace_model.get("model", {}))
        workspace_components = model.get("components", [])
        containers = {c.get("id", "") for c in model.get("containers", [])}

        fixed_components: list[dict[str, Any]] = []
        for comp in workspace_components:
            cid = comp.get("id", "")
            if cid not in (issue.node_ids or []):
                continue
            props = comp.get("properties", {})
            current = props.get("container_id", "")
            if current and current in containers:
                continue
            # Prefer registry container_id
            reg_info = registry_components.get(cid, {})
            new_container = reg_info.get("container_id", "")
            if not new_container:
                new_container = self._infer_from_code(cid, context)
            if new_container and new_container in containers:
                fixed_components.append({"id": cid, "new_container": new_container})

        if not fixed_components:
            return []

        new_model = self._patch_model(workspace_model, fixed_components)
        new_dsl = yaml.dump(new_model, allow_unicode=True, sort_keys=False, width=120)

        return [
            ChangeSet(
                action="EDIT_DSL",
                target_path=f"dsl://{project_id}",
                before=yaml.dump(workspace_model, allow_unicode=True, sort_keys=False, width=120),
                after=new_dsl,
                rationale="修正 L3 组件引用的 container_id，使其指向已定义的 L2 容器",
                risk_level=RiskLevel.LOW,
                auto_applicable=True,
                requires_confirmation=True,
                issue_id=issue.issue_id,
            )
        ]

    @staticmethod
    def _infer_from_code(component_id: str, context: dict[str, Any]) -> str:
        """Infer container from code file path of the component."""
        registry = context.get("registry") or {}
        info = registry.get("components", {}).get(component_id, {})
        source_file = info.get("source_file") or info.get("source_code_file", "")
        path = source_file.lower()
        if "frontend" in path:
            return "frontend-spa"
        if "c4" in path:
            return "c4-dsl-engine"
        if "wireframe" in path or "sketch" in path:
            return "wireframe-engine"
        if "scheduler" in path or "engine" in path:
            return "skill-orchestrator"
        if "backend" in path or "app/" in path:
            return "backend-api"
        return ""

    @staticmethod
    def _patch_model(
        workspace_model: dict[str, Any],
        fixes: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Return a new workspace dict with updated container_ids."""
        import copy

        new_model = copy.deepcopy(workspace_model)
        model = new_model.get("workspace", {}).get("model", new_model.get("model", {}))
        fix_map = {f["id"]: f["new_container"] for f in fixes}
        for comp in model.get("components", []):
            cid = comp.get("id", "")
            if cid in fix_map:
                comp.setdefault("properties", {})["container_id"] = fix_map[cid]
        return new_model
