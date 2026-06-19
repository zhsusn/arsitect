"""C4Renderer — backend DSL to Mermaid converter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.c4.analyzer import C4Analyzer
from app.c4.code_scanner import CodeScanner
from app.c4.consistency_checker import ConsistencyChecker
from app.c4.dsl_manager import C4DSLManager
from app.docforge.c4_assembler import C4Workspace


@dataclass
class MermaidOutput:
    """Mermaid rendering result."""

    mermaid_code: str
    view_level: str
    node_count: int
    edge_count: int
    analysis_report: dict[str, Any] | None = None
    consistency_report: dict[str, Any] | None = None


class C4Renderer:
    """Render C4 workspace to Mermaid diagram."""

    def __init__(self, dsl_manager: C4DSLManager) -> None:
        self.dsl = dsl_manager

    async def render(
        self,
        project_id: str,
        view_level: str = "L2",
        expanded_containers: list[str] | None = None,
    ) -> MermaidOutput:
        workspace = await self.dsl.read_workspace(project_id)
        if not workspace:
            return MermaidOutput("graph TD\n  A[No C4 DSL found]", view_level, 0, 0)
        if view_level == "L1":
            result = self._render_l1(workspace)
        elif view_level == "L2":
            result = self._render_l2(workspace)
        elif view_level == "L3":
            result = self._render_l3(workspace, expanded_containers)
        elif view_level == "L4":
            result = self._render_l4(workspace)
        else:
            result = self._render_l2(workspace)

        # Run structural analysis (best-effort; never block rendering)
        try:
            analyzer = C4Analyzer()
            report = analyzer.analyze(workspace, view_level)
            result.analysis_report = report.to_dict()
        except Exception:
            result.analysis_report = None

        # Run design ↔ code consistency check (best-effort)
        try:
            checker = ConsistencyChecker(CodeScanner())
            consistency = checker.check(workspace, view_level)
            result.consistency_report = consistency.to_dict()
        except Exception:
            result.consistency_report = None

        return result

    async def analyze_all(
        self,
        project_id: str,
    ) -> list[dict[str, Any]]:
        """Run structural analysis on all C4 levels (L1-L4).

        Returns a list of per-level analysis dicts.
        """
        workspace = await self.dsl.read_workspace(project_id)
        if not workspace:
            return []

        results: list[dict[str, Any]] = []
        analyzer = C4Analyzer()
        for level in ("L1", "L2", "L3", "L4"):
            try:
                report = analyzer.analyze(workspace, level)
                results.append(
                    {
                        "level": level,
                        "passed": report.passed,
                        "issues": report.to_dict()["issues"],
                        "summary": report.to_dict()["summary"],
                    }
                )
            except Exception:
                results.append(
                    {
                        "level": level,
                        "passed": True,
                        "issues": [],
                        "summary": {},
                    }
                )
        return results

    def _render_l1(self, ws: C4Workspace) -> MermaidOutput:
        lines = ["graph TB"]
        sid = ws.system["id"] if ws.system else "System"
        sname = ws.system.get("name", sid) if ws.system else sid
        lines.append(f'  {sid}["{sname}<br/>System"]')

        for actor in sorted(ws.actors, key=lambda x: x.get("id", "")):
            aid, aname = actor["id"], actor.get("name", actor["id"])
            lines.append(f'  {aid}(("{aname}<br/>Person"))')
            lines.append(f"  {aid} --> {sid}")

        for ext in sorted(ws.external_systems, key=lambda x: x.get("id", "")):
            eid, ename = ext["id"], ext.get("name", ext["id"])
            lines.append(f'  {eid}[["{ename}<br/>External System"]]')
            lines.append(f"  {sid} --> {eid}")

        node_count = 1 + len(ws.actors) + len(ws.external_systems)
        edge_count = len(ws.actors) + len(ws.external_systems)
        return MermaidOutput("\n".join(lines), "L1", node_count, edge_count)

    def _render_l2(self, ws: C4Workspace) -> MermaidOutput:
        lines = ["graph TB"]
        sid = ws.system["id"] if ws.system else "System"
        sname = ws.system.get("name", sid) if ws.system else sid
        lines.append(f"  subgraph {sid} [{sname}]")

        for c in sorted(ws.containers, key=lambda x: x.get("id", "")):
            cid, cname = c["id"], c.get("name", c["id"])
            tech = c.get("technology", "")
            lines.append(f'    {cid}(["{cname}<br/>[{tech}]"])')

        cids = {c["id"] for c in ws.containers}
        edge_count = 0
        for rel in ws.relationships:
            src = rel.get("source", "")
            dst = rel.get("target", "")
            desc = rel.get("description", "")
            if src in cids and dst in cids:
                if desc:
                    lines.append(f'    {src} -->|"{desc}"| {dst}')
                else:
                    lines.append(f"    {src} --> {dst}")
                edge_count += 1

        lines.append("  end")
        return MermaidOutput("\n".join(lines), "L2", len(ws.containers), edge_count)

    def _render_l3(
        self,
        ws: C4Workspace,
        expanded_containers: list[str] | None = None,
    ) -> MermaidOutput:
        lines = [
            "%%{init: {'flowchart': {'nodeSpacing': 80, 'rankSpacing': 100}}}%%",
            "graph TB",
        ]
        cmap: dict[str, list[dict[str, Any]]] = {}
        hidden_ids: set[str] = set()
        for comp in ws.components:
            if comp.get("properties", {}).get("intentional_orphan"):
                hidden_ids.add(comp["id"])
                continue
            cid = comp.get("properties", {}).get("container_id", "default")
            cmap.setdefault(cid, []).append(comp)

        # Determine expansion state: None = all expanded, [] = all collapsed
        all_expanded = expanded_containers is None
        expanded_set = set(expanded_containers or [])

        # Grid layout threshold: containers with more components are split
        # into multiple rows inside the subgraph to avoid a single long rank.
        grid_cols = 16

        # Render nodes (subgraphs or hub nodes)
        visible_nodes = 0
        for cid in sorted(cmap.keys()):
            comps = cmap[cid]
            if not comps:
                continue
            safe_cid = _mermaid_id(cid)
            is_expanded = all_expanded or cid in expanded_set
            # Metadata comment for frontend to parse container list and sizes
            lines.append(f"%% @container {cid} {len(comps)}")
            if is_expanded:
                lines.append(f'  subgraph {safe_cid} ["Container: {cid}"]')
                if len(comps) > grid_cols:
                    # Multi-row grid: each row is a nested LR subgraph
                    lines.append("    direction TB")
                    for ridx in range(0, len(comps), grid_cols):
                        row_id = f"{safe_cid}_row{ridx // grid_cols}"
                        row_comps = comps[ridx : ridx + grid_cols]
                        start_idx = ridx + 1
                        end_idx = min(ridx + grid_cols, len(comps))
                        lines.append(f'    subgraph {row_id} ["{cid} ({start_idx}~{end_idx})"]')
                        lines.append("      direction LR")
                        for comp in row_comps:
                            comp_id = _mermaid_id(comp["id"])
                            lines.append(f'        {comp_id}["{comp.get("name", comp["id"])}"]')
                        lines.append("    end")
                else:
                    lines.append("    direction LR")
                    for comp in comps:
                        comp_id = _mermaid_id(comp["id"])
                        lines.append(f'    {comp_id}["{comp.get("name", comp["id"])}"]')
                lines.append("  end")
                visible_nodes += len(comps)
            else:
                hub_id = f"{safe_cid}_hub"
                lines.append(f'  {hub_id}["{cid}<br/>({len(comps)} components)"]')
                visible_nodes += 1

        # Build component -> container mapping for visible components only
        comp_to_container: dict[str, str] = {}
        for comp in ws.components:
            if comp["id"] in hidden_ids:
                continue
            cid = comp.get("properties", {}).get("container_id", "default")
            comp_to_container[comp["id"]] = cid

        # Render relationships with container collapsing logic
        edge_count = 0
        seen_hub_edges: set[tuple[str, str]] = set()
        for rel in ws.relationships:
            src = rel.get("source", "")
            dst = rel.get("target", "")
            desc = rel.get("description", "")
            if src in hidden_ids or dst in hidden_ids:
                continue
            src_cid = comp_to_container.get(src)
            dst_cid = comp_to_container.get(dst)
            if not src_cid or not dst_cid:
                continue

            src_expanded = all_expanded or src_cid in expanded_set
            dst_expanded = all_expanded or dst_cid in expanded_set

            if src_cid == dst_cid:
                # Intra-container relationship
                if src_expanded:
                    if desc:
                        lines.append(f'  {_mermaid_id(src)} -->|"{desc}"| {_mermaid_id(dst)}')
                    else:
                        lines.append(f"  {_mermaid_id(src)} --> {_mermaid_id(dst)}")
                    edge_count += 1
            else:
                # Cross-container relationship
                if src_expanded and dst_expanded:
                    if desc:
                        lines.append(f'  {_mermaid_id(src)} -->|"{desc}"| {_mermaid_id(dst)}')
                    else:
                        lines.append(f"  {_mermaid_id(src)} --> {_mermaid_id(dst)}")
                    edge_count += 1
                else:
                    src_node = _mermaid_id(src) if src_expanded else f"{_mermaid_id(src_cid)}_hub"
                    dst_node = _mermaid_id(dst) if dst_expanded else f"{_mermaid_id(dst_cid)}_hub"
                    edge_key = (src_node, dst_node)
                    if edge_key not in seen_hub_edges:
                        seen_hub_edges.add(edge_key)
                        lines.append(f"  {src_node} --> {dst_node}")
                        edge_count += 1

        return MermaidOutput("\n".join(lines), "L3", visible_nodes, edge_count)

    def _render_l4(self, ws: C4Workspace) -> MermaidOutput:
        if not ws.code_elements:
            return MermaidOutput(
                'graph TD\n  A["暂无代码级数据<br/>L4 代码视图需要代码分析数据源"]',
                "L4",
                0,
                0,
            )
        lines = ["graph TB"]
        cmap: dict[str, list[dict[str, Any]]] = {}
        for elem in ws.code_elements:
            cid = elem.get("properties", {}).get("container_id", "default")
            cmap.setdefault(cid, []).append(elem)

        for cid in sorted(cmap.keys()):
            elems = cmap[cid]
            safe_cid = _mermaid_id(cid)
            lines.append(f'  subgraph {safe_cid} ["Container: {cid}"]')
            for elem in elems:
                elem_id = _mermaid_id(elem["id"])
                elem_name = elem.get("name", elem["id"])
                elem_type = elem.get("type", "Code")
                lines.append(f'    {elem_id}["{elem_name}<br/>[{elem_type}]"]')
            lines.append("  end")

        return MermaidOutput("\n".join(lines), "L4", len(ws.code_elements), 0)


def _mermaid_id(raw: str) -> str:
    import re

    text = re.sub(r"[^a-zA-Z0-9_]", "_", raw)
    if text in (
        "default",
        "graph",
        "subgraph",
        "end",
        "direction",
        "style",
        "classDef",
        "linkStyle",
    ):
        text = f"_{text}"
    return text
