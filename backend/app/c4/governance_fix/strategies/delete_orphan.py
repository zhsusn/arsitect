"""Strategy: remove orphan code files or DSL nodes."""

from __future__ import annotations

from typing import Any

import yaml

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class DeleteOrphanStrategy(FixStrategy):
    """Delete orphan code files or DSL nodes that have no upstream/downstream references."""

    def supports(self, issue: GovernanceIssue) -> bool:
        return issue.rule_id in (
            "ORPHAN-001",
            "ORPHAN-002",
            "C4-ORPHAN-001",
            "C4-ORPHAN-002",
        ) and issue.root_cause in (
            RootCause.CODE_DEAD,
            RootCause.DSL_DEPRECATED,
        )

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        if issue.rule_id in ("ORPHAN-001", "C4-ORPHAN-001"):
            changes: list[ChangeSet] = []
            # Prefer the explicit code entity id; otherwise try each orphan node id.
            targets = [issue.code_entity_id] if issue.code_entity_id else (issue.node_ids or [])
            for node_id in targets:
                if not node_id:
                    continue
                code_entity = self._find_code_entity(node_id, context)
                file_path = code_entity.get("file_path") if code_entity else ""
                if file_path:
                    changes.append(
                        ChangeSet(
                            action="DELETE_FILE",
                            target_path=file_path,
                            before="",
                            after="",
                            rationale=f"代码实体 '{node_id}' 无引用，且已确认废弃，建议删除文件",
                            risk_level=RiskLevel.HIGH,
                            auto_applicable=False,
                            requires_confirmation=True,
                            issue_id=issue.issue_id,
                        )
                    )
                else:
                    # No matching code entity: propose removing the DSL node.
                    workspace_model = context.get("workspace_model") or {}
                    new_model = self._remove_node(workspace_model, node_id)
                    if new_model is not None:
                        changes.append(
                            ChangeSet(
                                action="EDIT_DSL",
                                target_path=f"dsl://{project_id}",
                                before=yaml.dump(
                                    workspace_model, allow_unicode=True, sort_keys=False, width=120
                                ),
                                after=yaml.dump(
                                    new_model, allow_unicode=True, sort_keys=False, width=120
                                ),
                                rationale=f"C4 节点 '{node_id}' 在代码与 DSL 中均无关联，建议从 DSL 中移除",
                                risk_level=RiskLevel.HIGH,
                                auto_applicable=False,
                                requires_confirmation=True,
                                issue_id=issue.issue_id,
                            )
                        )
            return changes

        # ORPHAN-002 / C4-ORPHAN-002: remove DSL node.
        workspace_model = context.get("workspace_model") or {}
        node_id = issue.c4_node_id or (issue.node_ids[0] if issue.node_ids else "")
        new_model = self._remove_node(workspace_model, node_id)
        if new_model is None:
            return []
        return [
            ChangeSet(
                action="EDIT_DSL",
                target_path=f"dsl://{project_id}",
                before=yaml.dump(workspace_model, allow_unicode=True, sort_keys=False, width=120),
                after=yaml.dump(new_model, allow_unicode=True, sort_keys=False, width=120),
                rationale=f"C4 节点 '{issue.c4_node_id}' 无代码/容器映射，已废弃，建议从 DSL 中移除",
                risk_level=RiskLevel.HIGH,
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
            if e_name == name_lower:
                return entity
        return None

    @staticmethod
    def _remove_node(workspace_model: dict[str, Any], node_id: str | None) -> dict[str, Any] | None:
        if not node_id:
            return None
        import copy

        new_model: dict[str, Any] = copy.deepcopy(workspace_model)
        model = new_model.get("workspace", {}).get("model", new_model.get("model", {}))
        modified = False
        for key in ("containers", "components", "people", "softwareSystems"):
            items = model.get(key, [])
            before = len(items)
            model[key] = [item for item in items if item.get("id") != node_id]
            if len(model[key]) != before:
                modified = True
        return new_model if modified else None
