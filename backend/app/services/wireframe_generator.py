"""WireframeGenerator — DomainMapper + LayoutPlanner + NavigationLinker.

Based on DR-019 WireframeEngine three-agent architecture.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class C4Node:
    """从 Mermaid DSL 解析出的节点."""

    node_id: str
    label: str
    shape: str  # rect, circle, stadium, etc.


@dataclass
class C4Edge:
    """从 Mermaid DSL 解析出的边."""

    source: str
    target: str
    label: str | None


@dataclass
class MappedPage:
    """DomainMapper 输出：领域实体到页面类型的映射."""

    entity_id: str
    entity_name: str
    page_type: str
    confidence: int
    mapping_source: str  # auto, manual, low_conf, uncertain


@dataclass
class WireframePageData:
    """LayoutPlanner 输出：单页线框图数据."""

    page_id: str
    entity_id: str
    entity_name: str
    page_type: str
    confidence: int
    mapping_source: str
    svg_content: str
    layout_json: str


@dataclass
class NavLinkData:
    """NavigationLinker 输出：页面跳转关系."""

    source_entity_id: str
    target_entity_id: str
    relation_strength: str
    interface_count: int


# ------------------------------------------------------------------
# Mermaid DSL Parser
# ------------------------------------------------------------------

_MERMAID_NODE_RE = re.compile(
    r"^\s*([a-zA-Z0-9_]+)\s*\[(.*?)\]",
    re.MULTILINE,
)
_MERMAID_EDGE_RE = re.compile(
    r"^\s*([a-zA-Z0-9_]+)\s*[-=]+>\s*([a-zA-Z0-9_]+)(?:\s*\|([^|]+)\|)?",
    re.MULTILINE,
)


def parse_mermaid_dsl(dsl_text: str) -> tuple[list[C4Node], list[C4Edge]]:
    """从 Mermaid graph/flowchart 文本中提取节点和边.

    Args:
        dsl_text: Mermaid DSL 字符串.

    Returns:
        (nodes, edges)
    """
    nodes: list[C4Node] = []
    seen_ids: set[str] = set()
    for m in _MERMAID_NODE_RE.finditer(dsl_text):
        nid = m.group(1).strip()
        label = m.group(2).strip()
        if nid not in seen_ids:
            seen_ids.add(nid)
            nodes.append(C4Node(node_id=nid, label=label, shape="rect"))

    edges: list[C4Edge] = []
    for line in dsl_text.splitlines():
        line = line.strip()
        if not line or line.startswith(("%%", "graph", "flowchart", "subgraph")):
            continue
        # Simple edge pattern: A --> B or A --- B
        em = re.match(
            r"^\s*([a-zA-Z0-9_]+)\s*(?:\[[^\]]+\])?\s*[-=]+>\s*([a-zA-Z0-9_]+)",
            line,
        )
        if em:
            src = em.group(1).strip()
            tgt = em.group(2).strip()
            # Extract optional label like A -->|label| B
            lbl_m = re.search(r"\|([^|]+)\|", line)
            label = lbl_m.group(1).strip() if lbl_m else None
            edges.append(C4Edge(source=src, target=tgt, label=label))

    return nodes, edges


# ------------------------------------------------------------------
# DomainMapper
# ------------------------------------------------------------------

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "LIST": ["列表", "list", "查询", "批量", "table", "grid", "记录"],
    "DETAIL": ["详情", "detail", "查看", "明细", "profile", "信息"],
    "DASHBOARD": ["仪表盘", "dashboard", "统计", "图表", "概览", "指标", "chart"],
    "FORM": ["表单", "form", "填写", "提交", "编辑", "创建", "新增", "input"],
    "MODAL": ["弹窗", "modal", "对话框", "dialog", "确认框", "alert"],
    "SEARCH": ["搜索", "search", "检索", "查找", "筛选", "filter"],
    "WIZARD": ["向导", "wizard", "步骤", "step", "流程", "分步"],
}


def domain_mapper(nodes: list[C4Node]) -> list[MappedPage]:
    """将 C4 节点映射为页面类型.

    Args:
        nodes: Mermaid 解析出的节点列表.

    Returns:
        映射结果列表，含置信度评分.
    """
    results: list[MappedPage] = []
    for node in nodes:
        text = f"{node.label} {node.node_id}".lower()
        scores: dict[str, int] = {}
        for pt, keywords in _DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            if score:
                scores[pt] = score

        if not scores:
            # Default: if it looks like a service/container, treat as LIST
            if any(k in text for k in ["service", "api", "app", "gateway", "服务", "应用"]):
                results.append(
                    MappedPage(
                        entity_id=node.node_id,
                        entity_name=node.label,
                        page_type="LIST",
                        confidence=60,
                        mapping_source="low_conf",
                    )
                )
            else:
                results.append(
                    MappedPage(
                        entity_id=node.node_id,
                        entity_name=node.label,
                        page_type="UNKNOWN",
                        confidence=0,
                        mapping_source="uncertain",
                    )
                )
            continue

        best_pt = max(scores, key=scores.get)  # type: ignore[type-arg]
        best_score = scores[best_pt]
        confidence = min(100, best_score * 25 + 20)
        source = "auto" if confidence >= 80 else "low_conf"
        results.append(
            MappedPage(
                entity_id=node.node_id,
                entity_name=node.label,
                page_type=best_pt,
                confidence=confidence,
                mapping_source=source,
            )
        )
    return results


# ------------------------------------------------------------------
# LayoutPlanner — SVG wireframe renderers
# ------------------------------------------------------------------

def _svg_rect(x: int, y: int, w: int, h: int, fill: str = "#fff", stroke: str = "#adb5bd", attrs: str = "") -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" {attrs}/>'


def _svg_text(x: int, y: int, text: str, size: int = 12, color: str = "#495057", anchor: str = "start", weight: str = "normal") -> str:
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
        f'text-anchor="{anchor}" font-weight="{weight}">{_esc(text)}</text>'
    )


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _layout_list(entity_name: str, w: int = 640) -> str:
    h = 380
    padding = 24
    header_h = 56
    row_h = 44
    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        _svg_rect(0, 0, w, h, fill="#f8f9fa", stroke="#dee2e6", attrs='stroke-width="2"'),
        _svg_text(padding, 36, entity_name, size=18, color="#212529", weight="bold"),
        # Search bar placeholder
        _svg_rect(padding, header_h, w - padding * 2, 36, fill="#fff", stroke="#ced4da"),
        _svg_text(padding + 8, header_h + 24, "搜索 / 筛选...", size=12, color="#adb5bd"),
    ]
    y = header_h + 52
    cols = ["名称", "状态", "更新时间", "操作"]
    col_w = (w - padding * 2) // len(cols)
    # Header row
    lines.append(_svg_rect(padding, y, w - padding * 2, row_h, fill="#e9ecef", stroke="#adb5bd"))
    for i, c in enumerate(cols):
        cx = padding + col_w * i + col_w // 2
        lines.append(_svg_text(cx, y + 28, c, size=12, color="#495057", anchor="middle", weight="bold"))
    y += row_h
    for _ in range(4):
        lines.append(_svg_rect(padding, y, w - padding * 2, row_h, fill="#fff", stroke="#dee2e6"))
        for i in range(len(cols)):
            cx = padding + col_w * i + col_w // 2
            lines.append(_svg_text(cx, y + 28, "---", size=12, color="#adb5bd", anchor="middle"))
        y += row_h
    lines.append("</svg>")
    return "\n".join(lines)


def _layout_detail(entity_name: str, w: int = 480) -> str:
    h = 360
    padding = 24
    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        _svg_rect(0, 0, w, h, fill="#f8f9fa", stroke="#dee2e6", attrs='stroke-width="2"'),
        _svg_text(padding, 36, entity_name, size=18, color="#212529", weight="bold"),
        _svg_text(padding, 58, "详情页", size=12, color="#868e96"),
    ]
    y = 80
    for i in range(6):
        lines.append(_svg_text(padding, y + 18, f"属性 {i + 1}:", size=12, color="#868e96"))
        lines.append(_svg_rect(padding + 80, y, w - padding * 2 - 80, 28, fill="#fff", stroke="#ced4da", attrs='stroke-dasharray="3 3"'))
        y += 42
    lines.append("</svg>")
    return "\n".join(lines)


def _layout_dashboard(entity_name: str, w: int = 640) -> str:
    h = 400
    padding = 24
    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        _svg_rect(0, 0, w, h, fill="#f8f9fa", stroke="#dee2e6", attrs='stroke-width="2"'),
        _svg_text(padding, 36, entity_name, size=18, color="#212529", weight="bold"),
    ]
    cards = [
        (padding, 60, (w - padding * 3) // 2, 140),
        (padding + (w - padding * 3) // 2 + padding, 60, (w - padding * 3) // 2, 140),
        (padding, 216, (w - padding * 3) // 2, 140),
        (padding + (w - padding * 3) // 2 + padding, 216, (w - padding * 3) // 2, 140),
    ]
    for cx, cy, cw, ch in cards:
        lines.append(_svg_rect(cx, cy, cw, ch, fill="#fff", stroke="#adb5bd", attrs='rx="4"'))
        lines.append(_svg_text(cx + 12, cy + 28, "指标卡片", size=13, color="#868e96"))
        lines.append(_svg_text(cx + 12, cy + 72, "--", size=28, color="#495057"))
    lines.append("</svg>")
    return "\n".join(lines)


def _layout_form(entity_name: str, w: int = 480) -> str:
    h = 400
    padding = 24
    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        _svg_rect(0, 0, w, h, fill="#f8f9fa", stroke="#dee2e6", attrs='stroke-width="2"'),
        _svg_text(padding, 36, entity_name, size=18, color="#212529", weight="bold"),
    ]
    y = 64
    for i in range(5):
        lines.append(_svg_text(padding, y + 18, f"字段 {i + 1}", size=12, color="#868e96"))
        lines.append(_svg_rect(padding + 70, y, w - padding * 2 - 70, 32, fill="#fff", stroke="#ced4da"))
        y += 48
    y += 8
    lines.append(_svg_rect(padding, y, 90, 36, fill="#e9ecef", stroke="#495057", attrs='rx="4"'))
    lines.append(_svg_text(padding + 45, y + 24, "提交", size=14, color="#212529", anchor="middle"))
    lines.append(_svg_rect(padding + 110, y, 90, 36, fill="#fff", stroke="#adb5bd", attrs='rx="4"'))
    lines.append(_svg_text(padding + 155, y + 24, "取消", size=14, color="#495057", anchor="middle"))
    lines.append("</svg>")
    return "\n".join(lines)


def _layout_modal(entity_name: str, w: int = 400) -> str:
    h = 220
    cx = 40
    cy = 30
    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<rect width="100%" height="100%" fill="rgba(0,0,0,0.04)"/>',
        _svg_rect(cx, cy, w - cx * 2, h - cy * 2, fill="#fff", stroke="#495057", attrs='stroke-width="2" rx="6"'),
        _svg_text(cx + 20, cy + 32, entity_name, size=15, color="#212529", weight="bold"),
        _svg_text(cx + 20, cy + 70, "提示内容占位...", size=13, color="#868e96"),
        _svg_rect(w - cx - 90, h - cy - 48, 70, 32, fill="#e9ecef", stroke="#495057", attrs='rx="4"'),
        _svg_text(w - cx - 55, h - cy - 26, "确认", size=12, color="#212529", anchor="middle"),
        _svg_rect(w - cx - 170, h - cy - 48, 70, 32, fill="#fff", stroke="#adb5bd", attrs='rx="4"'),
        _svg_text(w - cx - 135, h - cy - 26, "取消", size=12, color="#495057", anchor="middle"),
        "</svg>",
    ]
    return "\n".join(lines)


def _layout_search(entity_name: str, w: int = 600) -> str:
    h = 300
    padding = 24
    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        _svg_rect(0, 0, w, h, fill="#f8f9fa", stroke="#dee2e6", attrs='stroke-width="2"'),
        _svg_text(padding, 36, entity_name, size=18, color="#212529", weight="bold"),
        _svg_rect(padding, 60, w - padding * 2 - 90, 36, fill="#fff", stroke="#ced4da"),
        _svg_text(padding + 8, 84, "关键词...", size=13, color="#adb5bd"),
        _svg_rect(w - padding - 80, 60, 80, 36, fill="#e9ecef", stroke="#495057", attrs='rx="4"'),
        _svg_text(w - padding - 40, 84, "搜索", size=13, color="#212529", anchor="middle"),
    ]
    y = 120
    for i in range(3):
        lines.append(_svg_rect(padding, y, 120, 28, fill="#fff", stroke="#adb5bd", attrs='stroke-dasharray="3 3"'))
        lines.append(_svg_text(padding + 8, y + 19, f"条件 {i + 1}", size=11, color="#868e96"))
        y += 44
    lines.append("</svg>")
    return "\n".join(lines)


def _layout_wizard(entity_name: str, w: int = 560) -> str:
    h = 280
    padding = 24
    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        _svg_rect(0, 0, w, h, fill="#f8f9fa", stroke="#dee2e6", attrs='stroke-width="2"'),
        _svg_text(padding, 36, entity_name, size=18, color="#212529", weight="bold"),
    ]
    y = 70
    steps = ["步骤 1", "步骤 2", "步骤 3"]
    step_w = (w - padding * 2 - 40) // len(steps)
    for i, step in enumerate(steps):
        sx = padding + i * (step_w + 20)
        color = "#495057" if i == 0 else "#dee2e6"
        text_color = "#fff" if i == 0 else "#868e96"
        lines.append(f'<circle cx="{sx + 12}" cy="{y + 12}" r="12" fill="{color}"/>')
        lines.append(_svg_text(sx + 12, y + 17, str(i + 1), size=11, color=text_color, anchor="middle"))
        lines.append(_svg_text(sx + 12, y + 40, step, size=11, color="#495057", anchor="middle"))
        if i < len(steps) - 1:
            lines.append(f'<line x1="{sx + 28}" y1="{y + 12}" x2="{sx + step_w + 4}" y2="{y + 12}" stroke="#dee2e6" stroke-width="2"/>')
    lines.append("</svg>")
    return "\n".join(lines)


def _layout_unknown(entity_name: str, w: int = 480) -> str:
    h = 200
    padding = 24
    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        _svg_rect(0, 0, w, h, fill="#f8f9fa", stroke="#dee2e6", attrs='stroke-width="2"'),
        _svg_text(padding, 36, entity_name, size=18, color="#212529", weight="bold"),
        _svg_text(padding, 70, "页面类型待确认", size=13, color="#868e96"),
        _svg_rect(padding, 100, w - padding * 2, 60, fill="#fff", stroke="#adb5bd", attrs='stroke-dasharray="4 2"'),
        _svg_text(padding + 8, 138, "请人工指定页面类型后重新生成", size=12, color="#adb5bd"),
        "</svg>",
    ]
    return "\n".join(lines)


_LAYOUT_RENDERERS: dict[str, callable] = {  # type: ignore[type-arg]
    "LIST": _layout_list,
    "DETAIL": _layout_detail,
    "DASHBOARD": _layout_dashboard,
    "FORM": _layout_form,
    "MODAL": _layout_modal,
    "SEARCH": _layout_search,
    "WIZARD": _layout_wizard,
    "UNKNOWN": _layout_unknown,
}


def layout_planner(mapped_pages: list[MappedPage]) -> list[WireframePageData]:
    """为已映射的页面生成 SVG 线框图.

    Args:
        mapped_pages: DomainMapper 输出.

    Returns:
        线框图页面数据列表.
    """
    results: list[WireframePageData] = []
    for mp in mapped_pages:
        renderer = _LAYOUT_RENDERERS.get(mp.page_type, _layout_unknown)
        svg = renderer(mp.entity_name)
        layout = {
            "page_type": mp.page_type,
            "title": mp.entity_name,
            "regions": [{"name": "标题区", "ratio": 0.1}, {"name": "内容区", "ratio": 0.75}, {"name": "操作区", "ratio": 0.15}],
        }
        results.append(
            WireframePageData(
                page_id=f"wfpage-{mp.entity_id}",
                entity_id=mp.entity_id,
                entity_name=mp.entity_name,
                page_type=mp.page_type,
                confidence=mp.confidence,
                mapping_source=mp.mapping_source,
                svg_content=svg,
                layout_json=json.dumps(layout, ensure_ascii=False),
            )
        )
    return results


# ------------------------------------------------------------------
# NavigationLinker
# ------------------------------------------------------------------

def navigation_linker(
    mapped_pages: list[MappedPage], edges: list[C4Edge]
) -> list[NavLinkData]:
    """基于 C4 边关系建立页面跳转关系.

    Args:
        mapped_pages: DomainMapper 输出.
        edges: Mermaid 解析出的边.

    Returns:
        跳转关系列表.
    """
    page_ids = {mp.entity_id for mp in mapped_pages}
    links: list[NavLinkData] = []
    for edge in edges:
        if edge.source in page_ids and edge.target in page_ids:
            # Simple heuristic: if edge label contains write operations -> strong
            label = (edge.label or "").lower()
            is_strong = any(k in label for k in ["创建", "提交", "更新", "删除", "post", "put", "delete", "write"])
            links.append(
                NavLinkData(
                    source_entity_id=edge.source,
                    target_entity_id=edge.target,
                    relation_strength="strong" if is_strong else "weak",
                    interface_count=1,
                )
            )
    return links


# ------------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------------

def generate_wireframe_from_c4(dsl_text: str) -> dict[str, Any]:
    """完整的 WireframeEngine 三阶段流水线.

    Args:
        dsl_text: C4 DSL Mermaid 文本.

    Returns:
        {"pages": [...], "nav_links": [...], "summary": {...}}
    """
    nodes, edges = parse_mermaid_dsl(dsl_text)
    mapped = domain_mapper(nodes)
    pages = layout_planner(mapped)
    nav_links = navigation_linker(mapped, edges)

    summary = {
        "total_pages": len(pages),
        "avg_confidence": round(sum(p.confidence for p in mapped) / max(1, len(mapped)), 1),
        "uncertain_count": sum(1 for p in mapped if p.mapping_source == "uncertain"),
        "nav_link_count": len(nav_links),
    }

    return {
        "pages": [p.__dict__ for p in pages],
        "nav_links": [link.__dict__ for link in nav_links],
        "summary": summary,
    }
