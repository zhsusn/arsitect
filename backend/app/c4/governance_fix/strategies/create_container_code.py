"""Strategy: create a placeholder code module for a C4 container without code."""

from __future__ import annotations

from typing import Any

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class CreateContainerCodeStrategy(FixStrategy):
    """Create a skeleton directory/file for a container that exists in DSL but not in code."""

    def supports(self, issue: GovernanceIssue) -> bool:
        return issue.rule_id in ("CON-C2M-001",) and issue.root_cause == RootCause.CODE_MISSING

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        container_id = issue.c4_node_id or issue.code_entity_id or ""
        if not container_id and issue.node_ids:
            container_id = issue.node_ids[0]
        if not container_id:
            return []

        rel_path, content = self._skeleton(container_id)
        return [
            ChangeSet(
                action="CREATE_FILE",
                target_path=rel_path,
                before="",
                after=content,
                rationale=f"容器 '{container_id}' 在 C4 中已定义但缺少对应代码模块，生成最小占位文件",
                risk_level=RiskLevel.MEDIUM,
                auto_applicable=False,
                requires_confirmation=True,
                issue_id=issue.issue_id,
            )
        ]

    @staticmethod
    def _skeleton(container_id: str) -> tuple[str, str]:
        cid = container_id.lower().replace("-", "_")
        if "frontend" in cid or cid.endswith("spa"):
            rel = f"frontend/src/containers/{container_id}/index.tsx"
            content = f"""import React from 'react'

export interface {container_id.title().replace('-', '')}Props {{
  // TODO: define props
}}

/**
 * TODO: implement {container_id} container
 */
export const {container_id.title().replace('-', '')}: React.FC<{container_id.title().replace('-', '')}Props> = () => {{
  return <div>{container_id}</div>
}}

export default {container_id.title().replace('-', '')}
"""
        else:
            rel = f"backend/app/{cid}/__init__.py"
            content = f'"""{container_id} container module."""\n\n# TODO: implement {container_id} container logic\n'
        return rel, content
