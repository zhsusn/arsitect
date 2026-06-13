"""C4Analyzer — architecture diagram rule checking engine.

Analyzes rendered C4 diagrams for structural issues:
- Orphan nodes (defined but no relationships)
- Circular dependencies
- Naming convention violations
- Level consistency (L3 components without valid L2 container)
- Disconnected subgraphs
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from app.docforge.c4_assembler import C4Workspace


@dataclass
class AnalysisIssue:
    """Single analysis finding."""

    rule_id: str
    severity: str  # BLOCKER | ERROR | WARNING | INFO
    message: str
    node_ids: list[str] = field(default_factory=list)
    fix_hint: str = ""


@dataclass
class AnalysisReport:
    """Complete analysis result."""

    passed: bool
    issues: list[AnalysisIssue] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON response."""
        return {
            "passed": self.passed,
            "issues": [
                {
                    "rule_id": i.rule_id,
                    "severity": i.severity,
                    "message": i.message,
                    "node_ids": i.node_ids,
                    "fix_hint": i.fix_hint,
                }
                for i in self.issues
            ],
            "summary": self.summary,
        }


class C4Analyzer:
    """Run static analysis rules against a C4 workspace."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        ws: C4Workspace,
        level: str,
    ) -> AnalysisReport:
        """Run all applicable rules for the given view level.

        Args:
            ws: C4 workspace model.
            level: View level (L1-L4).

        Returns:
            Analysis report with findings.
        """
        issues: list[AnalysisIssue] = []

        # Build directed graph from relationships
        graph = self._build_graph(ws)
        all_node_ids = self._collect_node_ids(ws, level)

        # Rule: orphan nodes
        issues.extend(self._check_orphan_nodes(all_node_ids, graph, ws, level))

        # Rule: circular dependencies (L2 and L3 only)
        if level in ("L2", "L3"):
            issues.extend(self._check_circular_dependencies(graph, level))

        # Rule: naming conventions
        issues.extend(self._check_naming_conventions(ws, level))

        # Rule: level consistency (L3 only)
        if level == "L3":
            issues.extend(self._check_level_consistency(ws))

        # Rule: disconnected subgraphs (L2+ only; L1 naturally has disconnected actors)
        if level != "L1":
            issues.extend(self._check_disconnected_subgraphs(graph, all_node_ids))

        # Build summary
        severity_order = ["BLOCKER", "ERROR", "WARNING", "INFO"]
        summary = {s: sum(1 for i in issues if i.severity == s) for s in severity_order}
        passed = summary["BLOCKER"] == 0 and summary["ERROR"] == 0

        return AnalysisReport(passed=passed, issues=issues, summary=summary)

    # ------------------------------------------------------------------
    # Rule implementations
    # ------------------------------------------------------------------

    def _check_orphan_nodes(
        self,
        all_node_ids: set[str],
        graph: dict[str, set[str]],
        ws: C4Workspace,
        level: str,
    ) -> list[AnalysisIssue]:
        """Find nodes that have no incoming or outgoing edges.

        Context-aware:
        - L1: Actor/ExternalSystem are often one-way touchpoints → INFO
        - L3: Utility/config components legitimately have no relations → INFO if intentional
        - L2/L4: Containers and code elements should have relations → WARNING
        """
        issues: list[AnalysisIssue] = []
        connected: set[str] = set()
        for src, targets in graph.items():
            connected.add(src)
            connected.update(targets)
        orphans = sorted(all_node_ids - connected)
        if not orphans:
            return issues

        # Filter out intentionally orphaned nodes
        effective_orphans: list[str] = []
        intentional: list[str] = []
        for nid in orphans:
            node = self._find_node_by_id(ws, level, nid)
            props = node.get("properties", {}) if node else {}
            if props.get("intentional_orphan") or props.get("intentional_orphan") == "true":
                intentional.append(nid)
            else:
                effective_orphans.append(nid)

        if effective_orphans:
            severity = "WARNING" if level in ("L2", "L4") else "INFO"
            level_name = {"L1": "系统上下文", "L2": "容器", "L3": "组件", "L4": "代码"}.get(level, level)
            issues.append(
                AnalysisIssue(
                    rule_id="C4-ORPHAN-001",
                    severity=severity,
                    message=f"{level_name}层发现 {len(effective_orphans)} 个孤立节点（无关联关系）",
                    node_ids=effective_orphans,
                    fix_hint="为这些节点添加关系，或在 DSL properties 中设置 intentional_orphan: true 豁免",
                )
            )
        if intentional:
            issues.append(
                AnalysisIssue(
                    rule_id="C4-ORPHAN-002",
                    severity="INFO",
                    message=f"{len(intentional)} 个节点已标记为 intentional_orphan，跳过检查",
                    node_ids=intentional,
                    fix_hint="无需操作",
                )
            )
        return issues

    def _check_circular_dependencies(
        self,
        graph: dict[str, set[str]],
        level: str,
    ) -> list[AnalysisIssue]:
        """Detect cycles in the dependency graph."""
        issues: list[AnalysisIssue] = []
        cycles = self._find_cycles(graph)
        if cycles:
            for cycle in cycles[:5]:  # Report first 5 cycles only
                issues.append(
                    AnalysisIssue(
                        rule_id="C4-CYCLE-001",
                        severity="ERROR",
                        message=f"{level} 层发现循环依赖: {' → '.join(cycle)} → {cycle[0]}",
                        node_ids=list(cycle),
                        fix_hint="引入中间层或事件驱动架构打破循环，或使用依赖倒置原则",
                    )
                )
            if len(cycles) > 5:
                issues.append(
                    AnalysisIssue(
                        rule_id="C4-CYCLE-002",
                        severity="WARNING",
                        message=f"还有 {len(cycles) - 5} 个循环依赖未显示",
                        node_ids=[],
                        fix_hint="修复已显示的循环后重新分析",
                    )
                )
        return issues

    def _check_naming_conventions(
        self,
        ws: C4Workspace,
        level: str,
    ) -> list[AnalysisIssue]:
        """Check that node IDs follow naming conventions.

        Relaxed: only INFO since many projects use Chinese IDs or domain terms.
        """
        issues: list[AnalysisIssue] = []
        bad_ids: list[str] = []

        nodes = self._collect_nodes(ws, level)
        for node in nodes:
            nid = node.get("id", "")
            # Accept kebab-case, snake_case, or CamelCase
            if not all(c.isalnum() or c in "-_" for c in nid):
                bad_ids.append(nid)

        if bad_ids:
            issues.append(
                AnalysisIssue(
                    rule_id="C4-NAME-001",
                    severity="INFO",
                    message=f"{len(bad_ids)} 个节点 ID 包含特殊字符",
                    node_ids=bad_ids[:10],
                    fix_hint="建议使用 kebab-case / snake_case / CamelCase（如 backend-api）。如业务需要中文 ID，可在规则配置中忽略此规则",
                )
            )
        return issues

    def _check_level_consistency(
        self,
        ws: C4Workspace,
    ) -> list[AnalysisIssue]:
        """L3: all components must belong to a known L2 container."""
        issues: list[AnalysisIssue] = []
        container_ids = {c["id"] for c in ws.containers}
        bad_components: list[str] = []
        for comp in ws.components:
            cid = comp.get("properties", {}).get("container_id", "")
            if cid and cid not in container_ids:
                bad_components.append(comp["id"])
        if bad_components:
            issues.append(
                AnalysisIssue(
                    rule_id="C4-LEVEL-001",
                    severity="ERROR",
                    message=f"{len(bad_components)} 个 L3 组件引用了不存在的 L2 容器",
                    node_ids=bad_components[:10],
                    fix_hint="检查 component 的 container_id 属性，确保对应容器已在 L2 定义",
                )
            )
        return issues

    def _check_disconnected_subgraphs(
        self,
        graph: dict[str, set[str]],
        all_node_ids: set[str],
    ) -> list[AnalysisIssue]:
        """Detect multiple disconnected components in the graph."""
        issues: list[AnalysisIssue] = []
        if len(all_node_ids) <= 1:
            return issues

        # BFS to find connected components
        visited: set[str] = set()
        components: list[set[str]] = []

        for start in sorted(all_node_ids):
            if start in visited:
                continue
            comp = set()
            stack = [start]
            while stack:
                node = stack.pop()
                if node in comp:
                    continue
                comp.add(node)
                # Outgoing
                for neighbor in graph.get(node, set()):
                    if neighbor not in comp:
                        stack.append(neighbor)
                # Incoming
                for src, targets in graph.items():
                    if node in targets and src not in comp:
                        stack.append(src)
            visited.update(comp)
            components.append(comp)

        if len(components) > 1:
            comp_descs = [
                f"子图 {i+1} ({len(c)} 节点: {', '.join(sorted(c)[:3])}{'...' if len(c) > 3 else ''})"
                for i, c in enumerate(components)
            ]
            issues.append(
                AnalysisIssue(
                    rule_id="C4-DISCONN-001",
                    severity="WARNING",
                    message=f"图被拆分为 {len(components)} 个不连通的子图",
                    node_ids=[],
                    fix_hint=f"{'；'.join(comp_descs)}。建议检查各子图之间是否需要添加关系",
                )
            )
        return issues

    # ------------------------------------------------------------------
    # Graph helpers
    # ------------------------------------------------------------------

    def _build_graph(
        self,
        ws: C4Workspace,
    ) -> dict[str, set[str]]:
        """Build directed adjacency list from relationships."""
        graph: dict[str, set[str]] = defaultdict(set)
        for rel in ws.relationships:
            src = rel.get("source", "")
            dst = rel.get("target", "")
            if src and dst:
                graph[src].add(dst)
        return dict(graph)

    def _collect_node_ids(
        self,
        ws: C4Workspace,
        level: str,
    ) -> set[str]:
        """Collect all node IDs present at the given level."""
        ids: set[str] = set()
        if ws.system:
            ids.add(ws.system.get("id", ""))
        if level == "L1":
            for a in ws.actors:
                ids.add(a.get("id", ""))
            for e in ws.external_systems:
                ids.add(e.get("id", ""))
        elif level == "L2":
            for c in ws.containers:
                ids.add(c.get("id", ""))
        elif level == "L3":
            for c in ws.components:
                ids.add(c.get("id", ""))
        elif level == "L4":
            for e in ws.code_elements:
                ids.add(e.get("id", ""))
        return {i for i in ids if i}

    def _collect_nodes(
        self,
        ws: C4Workspace,
        level: str,
    ) -> list[dict[str, Any]]:
        """Collect all node objects at the given level."""
        if level == "L1":
            nodes = []
            if ws.system:
                nodes.append(ws.system)
            nodes.extend(ws.actors)
            nodes.extend(ws.external_systems)
            return nodes
        elif level == "L2":
            return list(ws.containers)
        elif level == "L3":
            return list(ws.components)
        elif level == "L4":
            return list(ws.code_elements)
        return []

    def _find_node_by_id(
        self,
        ws: C4Workspace,
        level: str,
        node_id: str,
    ) -> dict[str, Any] | None:
        """Find a node object by its ID at the given level."""
        for node in self._collect_nodes(ws, level):
            if node.get("id") == node_id:
                return node
        # Fallback: check system for L1
        if level == "L1" and ws.system and ws.system.get("id") == node_id:
            return ws.system
        return None

    def _find_cycles(
        self,
        graph: dict[str, set[str]],
    ) -> list[tuple[str, ...]]:
        """Find simple cycles in the directed graph (Tarjan-based DFS)."""
        cycles: list[tuple[str, ...]] = []
        visited: set[str] = set()
        rec_stack: list[str] = []
        rec_set: set[str] = set()

        def dfs(node: str) -> None:
            if node in rec_set:
                # Found cycle
                try:
                    idx = rec_stack.index(node)
                    cycle = tuple(rec_stack[idx:])
                    # Normalize: rotate to smallest element
                    min_idx = min(range(len(cycle)), key=lambda i: cycle[i])
                    normalized = tuple(cycle[min_idx:] + cycle[:min_idx])
                    if normalized not in seen_cycles:
                        seen_cycles.add(normalized)
                        cycles.append(normalized)
                except ValueError:
                    pass
                return
            if node in visited:
                return
            visited.add(node)
            rec_set.add(node)
            rec_stack.append(node)
            for neighbor in graph.get(node, set()):
                dfs(neighbor)
            rec_stack.pop()
            rec_set.remove(node)

        seen_cycles: set[tuple[str, ...]] = set()
        for node in sorted(graph.keys()):
            if node not in visited:
                dfs(node)
        return cycles
