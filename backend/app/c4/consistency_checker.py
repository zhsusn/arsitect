"""ConsistencyChecker — compare C4 design against actual code.

Detects mismatches between architecture documents and implementation:
- C4 containers without corresponding code directories
- C4 components without corresponding code classes/functions
- Code entities not defined in C4 design
- C4 relationships without corresponding code imports/calls
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.c4.code_scanner import CodeEntity, CodeScanner
from app.docforge.c4_assembler import C4Workspace


@dataclass
class ConsistencyIssue:
    """Single consistency finding."""

    rule_id: str
    severity: str
    message: str
    c4_node_id: str = ""
    code_entity_id: str = ""
    fix_hint: str = ""
    fix_action: str = ""  # UPDATE_DOC | UPDATE_CODE | BOTH


@dataclass
class ConsistencyReport:
    """Complete consistency check result."""

    passed: bool
    issues: list[ConsistencyIssue] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    code_scan_summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "issues": [
                {
                    "rule_id": i.rule_id,
                    "severity": i.severity,
                    "message": i.message,
                    "c4_node_id": i.c4_node_id,
                    "code_entity_id": i.code_entity_id,
                    "fix_hint": i.fix_hint,
                    "fix_action": i.fix_action,
                }
                for i in self.issues
            ],
            "summary": self.summary,
            "code_scan_summary": self.code_scan_summary,
        }


class ConsistencyChecker:
    """Check consistency between C4 design and code implementation."""

    def __init__(self, scanner: CodeScanner | None = None) -> None:
        self._scanner = scanner or CodeScanner()

    def check(
        self,
        ws: C4Workspace,
        level: str,
    ) -> ConsistencyReport:
        """Run consistency checks.

        Args:
            ws: C4 workspace from design documents.
            level: Current view level (L1-L4).

        Returns:
            Consistency report with mismatches.
        """
        issues: list[ConsistencyIssue] = []
        code_result = self._scanner.scan()
        code_entities = code_result.entities

        # Only run deep checks for L2-L4
        if level in ("L2", "L3", "L4"):
            issues.extend(self._check_containers_have_code(ws, code_entities))
            issues.extend(self._check_code_has_container(ws, code_entities))

        if level in ("L3", "L4"):
            issues.extend(self._check_components_have_code(ws, code_entities))
            issues.extend(self._check_code_has_component(ws, code_entities))

        # Always check: system context
        if level == "L1":
            issues.extend(self._check_system_context(ws, code_entities))

        severity_order = ["BLOCKER", "ERROR", "WARNING", "INFO"]
        summary = {s: sum(1 for i in issues if i.severity == s) for s in severity_order}
        passed = summary["BLOCKER"] == 0 and summary["ERROR"] == 0

        return ConsistencyReport(
            passed=passed,
            issues=issues,
            summary=summary,
            code_scan_summary=code_result.summary,
        )

    # ------------------------------------------------------------------
    # L2: Container ↔ Code directory consistency
    # ------------------------------------------------------------------

    def _check_containers_have_code(
        self,
        ws: C4Workspace,
        code_entities: list[CodeEntity],
    ) -> list[ConsistencyIssue]:
        """Each L2 container should have corresponding code modules."""
        issues: list[ConsistencyIssue] = []
        {e.id.lower() for e in code_entities}
        {e.name.lower() for e in code_entities}

        for container in ws.containers:
            cid = container.get("id", "")
            cname = container.get("name", cid)
            if not cid:
                continue
            # Heuristic: container id/name should appear in code path or entity name
            cid_lower = cid.lower().replace("-", "_").replace(".", "_")
            cname_lower = cname.lower().replace("-", "_").replace(".", "_")
            found = any(
                cid_lower in e.container_hint.lower()
                or cname_lower in e.container_hint.lower()
                or cid_lower in e.file_path.lower().replace("-", "_")
                or cname_lower in e.file_path.lower().replace("-", "_")
                for e in code_entities
            )
            if not found:
                issues.append(
                    ConsistencyIssue(
                        rule_id="CON-C2M-001",
                        severity="WARNING",
                        message=f"容器 '{cname}' 在代码中未找到对应模块",
                        c4_node_id=cid,
                        fix_hint=f"在 backend/app/ 或 frontend/src/ 下创建 '{cid}' 目录；或在设计文档中修正容器定义",
                        fix_action="UPDATE_DOC"
                        if self._is_likely_doc_issue(cid, ws)
                        else "UPDATE_CODE",
                    )
                )
        return issues

    def _check_code_has_container(
        self,
        ws: C4Workspace,
        code_entities: list[CodeEntity],
    ) -> list[ConsistencyIssue]:
        """Code modules should be defined as L2 containers in C4."""
        issues: list[ConsistencyIssue] = []
        container_ids = {c.get("id", "").lower() for c in ws.containers}
        container_names = {c.get("name", "").lower() for c in ws.containers}

        # Check major code directories that might represent containers
        seen_hints: set[str] = set()
        for entity in code_entities:
            hint = entity.container_hint.lower()
            if not hint or hint in seen_hints:
                continue
            seen_hints.add(hint)
            if hint not in container_ids and hint not in container_names and hint != "":
                # Skip if it's clearly a sub-module
                if hint in ("api", "services", "components", "pages", "utils"):
                    continue
                issues.append(
                    ConsistencyIssue(
                        rule_id="CON-M2C-001",
                        severity="WARNING",
                        message=f"代码目录 '{entity.container_hint}' 未在 C4 L2 中定义为容器",
                        code_entity_id=entity.id,
                        fix_hint="在概要设计文档中添加此容器定义，或在代码中调整目录命名",
                        fix_action="UPDATE_DOC",
                    )
                )
        return issues

    # ------------------------------------------------------------------
    # L3: Component ↔ Code class/function consistency
    # ------------------------------------------------------------------

    def _check_components_have_code(
        self,
        ws: C4Workspace,
        code_entities: list[CodeEntity],
    ) -> list[ConsistencyIssue]:
        """Each L3 component should have a corresponding code implementation."""
        issues: list[ConsistencyIssue] = []
        {e.name.lower() for e in code_entities}

        for comp in ws.components:
            comp_id = comp.get("id", "")
            comp_name = comp.get("name", comp_id)
            if not comp_id:
                continue
            name_lower = comp_name.lower().replace("-", "_")
            id_lower = comp_id.lower().replace("-", "_")
            found = any(
                name_lower == e.name.lower().replace("-", "_")
                or id_lower == e.name.lower().replace("-", "_")
                or name_lower in e.name.lower().replace("-", "_")
                or id_lower in e.name.lower().replace("-", "_")
                for e in code_entities
            )
            if not found:
                issues.append(
                    ConsistencyIssue(
                        rule_id="CON-C2F-001",
                        severity="WARNING",
                        message=f"组件 '{comp_name}' 在代码中未找到对应类/函数",
                        c4_node_id=comp_id,
                        fix_hint=f"在代码中实现 '{comp_name}' 组件；或在设计文档中移除/修正此组件",
                        fix_action="UPDATE_DOC"
                        if self._is_likely_doc_issue(comp_id, ws)
                        else "UPDATE_CODE",
                    )
                )
        return issues

    def _check_code_has_component(
        self,
        ws: C4Workspace,
        code_entities: list[CodeEntity],
    ) -> list[ConsistencyIssue]:
        """Major code classes/functions should be defined as L3 components."""
        issues: list[ConsistencyIssue] = []
        comp_names = {
            c.get("name", c.get("id", "")).lower().replace("-", "_") for c in ws.components
        }
        comp_ids = {c.get("id", "").lower().replace("-", "_") for c in ws.components}

        # Only check top-level classes/components (not internal helpers)
        for entity in code_entities:
            if entity.type not in ("class", "component", "service"):
                continue
            name_lower = entity.name.lower().replace("-", "_")
            if len(name_lower) <= 2:  # Skip short names
                continue
            if name_lower not in comp_names and name_lower not in comp_ids:
                # Allow partial match
                found = any(name_lower in cn or cn in name_lower for cn in comp_names | comp_ids)
                if not found:
                    issues.append(
                        ConsistencyIssue(
                            rule_id="CON-F2C-001",
                            severity="INFO",
                            message=f"代码实体 '{entity.name}' ({entity.language}) 未在 C4 L3 中定义为组件",
                            code_entity_id=entity.id,
                            fix_hint="在详细设计文档中添加此组件定义",
                            fix_action="UPDATE_DOC",
                        )
                    )
        return issues

    # ------------------------------------------------------------------
    # L1: System context
    # ------------------------------------------------------------------

    def _check_system_context(
        self,
        ws: C4Workspace,
        code_entities: list[CodeEntity],
    ) -> list[ConsistencyIssue]:
        """Check that the system has actual code representation."""
        issues: list[ConsistencyIssue] = []
        if not ws.system:
            issues.append(
                ConsistencyIssue(
                    rule_id="CON-SYS-001",
                    severity="ERROR",
                    message="C4 L1 缺少 System 定义",
                    fix_hint="在概要设计文档中定义系统边界和名称",
                    fix_action="UPDATE_DOC",
                )
            )
        elif not code_entities:
            issues.append(
                ConsistencyIssue(
                    rule_id="CON-SYS-002",
                    severity="ERROR",
                    message="项目代码目录为空或无法扫描",
                    fix_hint="确认 backend/app/ 和 frontend/src/ 目录存在且有代码文件",
                    fix_action="UPDATE_CODE",
                )
            )
        return issues

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_likely_doc_issue(node_id: str, ws: C4Workspace) -> bool:
        """Heuristic: if the node name looks like a placeholder, it's probably a doc issue."""
        nid = node_id.lower()
        placeholders = ("todo", "tbd", "placeholder", "unknown", "unnamed", "module", "component")
        if any(p in nid for p in placeholders):
            return True
        # If the node has no relationships, it's likely an incomplete doc entry
        rel_count = sum(
            1
            for r in ws.relationships
            if r.get("source", "").lower() == nid or r.get("target", "").lower() == nid
        )
        return rel_count == 0
