"""Strategy: generate code skeletons for missing components."""

from __future__ import annotations

from typing import Any

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class CreateCodeSkeletonStrategy(FixStrategy):
    """Create a .py or .tsx skeleton for a documented component without code."""

    _FRONTEND_SUFFIXES = ("button", "input", "badge", "view", "panel", "modal", "card")

    def supports(self, issue: GovernanceIssue) -> bool:
        return issue.rule_id == "CON-C2F-001" and issue.root_cause == RootCause.CODE_MISSING

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        comp_id = issue.c4_node_id or ""
        registry = context.get("registry") or {}
        info = registry.get("components", {}).get(comp_id, {})
        name = info.get("name") or comp_id
        container = info.get("container_id", "")

        if self._is_frontend(container, name):
            rel_path, content = self._frontend_skeleton(name)
        else:
            rel_path, content = self._backend_skeleton(name)

        return [
            ChangeSet(
                action="CREATE_FILE",
                target_path=rel_path,
                before="",
                after=content,
                rationale=f"为 C4 组件 '{name}' 生成代码骨架，仅含签名与 TODO，业务逻辑待人工补充",
                risk_level=RiskLevel.MEDIUM,
                auto_applicable=False,
                requires_confirmation=True,
                issue_id=issue.issue_id,
            )
        ]

    def _is_frontend(self, container: str, name: str) -> bool:
        if container == "frontend-spa":
            return True
        lower = name.lower()
        return any(lower.endswith(s) for s in self._FRONTEND_SUFFIXES)

    @staticmethod
    def _backend_skeleton(name: str) -> tuple[str, str]:
        """Return (relative_path, python_skeleton)."""
        snake = (
            "".join(["_" + c.lower() if c.isupper() else c for c in name])
            .lstrip("_")
            .replace("__", "_")
        )
        rel = f"backend/app/services/{snake}.py"
        content = f'"""{name} service skeleton."""\n\n\nclass {name}:\n    """TODO: implement {name}."""\n\n    def __init__(self) -> None:\n        pass\n\n    def process(self) -> None:\n        """TODO: add business logic."""\n        raise NotImplementedError\n'
        return rel, content

    @staticmethod
    def _frontend_skeleton(name: str) -> tuple[str, str]:
        """Return (relative_path, tsx_skeleton)."""
        rel = f"frontend/src/components/{name}.tsx"
        content = f"""import React from 'react'

export interface {name}Props {{
  // TODO: define props
}}

/**
 * TODO: implement {name}
 */
export const {name}: React.FC<{name}Props> = () => {{
  return (
    <div>
      {name}
    </div>
  )
}}

export default {name}
"""
        return rel, content
