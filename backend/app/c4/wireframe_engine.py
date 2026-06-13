"""WireframeEngine — SVG wireframe with page navigation graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.c4.baseline_store import C4BaselineStore


@dataclass
class WireframePage:
    """Single wireframe page."""

    page_id: str
    title: str
    page_type: str
    entity_id: str
    x: float = 0
    y: float = 0
    width: float = 240
    height: float = 180
    elements: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class NavigationEdge:
    """Page navigation edge."""

    source: str
    target: str
    label: str = ""
    strength: float = 1.0


@dataclass
class WireframeResult:
    """Wireframe generation result."""

    pages: list[WireframePage]
    edges: list[NavigationEdge]
    orphan_pages: list[str]
    svg_content: str


PAGE_TYPE_RULES: list[tuple[callable, str, float]] = [  # type: ignore[type-arg]
    (lambda e: "count" in str(e).lower() or "total" in str(e).lower(), "dashboard", 0.8),
    (lambda e: "AggregateRoot" in str(e), "list", 0.9),
    (lambda e: "id" in str(e).lower() and "name" in str(e).lower(), "detail", 0.7),
    (lambda e: "POST" in str(e) or "create" in str(e).lower(), "form", 0.8),
    (lambda e: "search" in str(e).lower(), "search", 0.9),
]

_COLORS = {
    "bg": "white",
    "border": "#333",
    "header": "#e3f2fd",
    "accent": "#1976d2",
    "types": {
        "list": "#e8f5e9",
        "detail": "#fff3e0",
        "form": "#fce4ec",
        "dashboard": "#f3e5f5",
        "search": "#e8eaf6",
    },
}


class WireframeEngine:
    """Generate SVG wireframe canvas with page nodes and navigation edges."""

    CANVAS_WIDTH = 1200
    CANVAS_HEIGHT = 800
    PAGE_WIDTH = 240
    PAGE_HEIGHT = 180

    def __init__(self, baseline_store: C4BaselineStore) -> None:
        self.store = baseline_store

    async def generate(
        self, project_id: str, module_id: str | None = None
    ) -> WireframeResult:
        entities = await self.store.get_l2_entities(project_id)
        if not entities:
            return WireframeResult([], [], [], "")
        pages = self._domain_mapper(entities)
        self._layout_planner(pages)
        edges = self._navigation_linker(pages)
        svg = self._render_svg(pages, edges)
        connected = set()
        for e in edges:
            connected.add(e.source)
            connected.add(e.target)
        orphans = [p.page_id for p in pages if p.page_id not in connected]
        return WireframeResult(pages, edges, orphans, svg)

    def _domain_mapper(self, entities: list[dict[str, Any]]) -> list[WireframePage]:
        pages: list[WireframePage] = []
        for entity in entities:
            eid = entity["id"]
            ename = entity.get("name", eid)
            page_type, _ = self._infer_page_type(entity)
            elements = self._generate_elements(page_type, entity)
            pages.append(
                WireframePage(
                    page_id=f"page_{eid}",
                    title=ename,
                    page_type=page_type,
                    entity_id=eid,
                    elements=elements,
                )
            )
        return pages

    def _infer_page_type(self, entity: dict[str, Any]) -> tuple[str, float]:
        entity_str = str(entity)
        for condition, page_type, confidence in PAGE_TYPE_RULES:
            if condition(entity_str):
                return page_type, confidence
        return "list", 0.5

    def _generate_elements(
        self, page_type: str, entity: dict[str, Any]
    ) -> list[dict[str, Any]]:
        name = entity.get("name", "")
        if page_type == "list":
            return [
                {"type": "header", "text": name, "x": 10, "y": 10},
                {"type": "search_bar", "placeholder": "Search...", "x": 10, "y": 40},
                {"type": "table", "x": 10, "y": 70, "rows": 5},
                {"type": "button", "text": "+ New", "x": 180, "y": 10},
            ]
        if page_type == "detail":
            return [
                {"type": "header", "text": name, "x": 10, "y": 10},
                {
                    "type": "field_group",
                    "x": 10,
                    "y": 40,
                    "fields": ["Name", "Status", "Created"],
                },
                {"type": "button", "text": "Edit", "x": 10, "y": 150},
            ]
        if page_type == "form":
            return [
                {"type": "header", "text": f"New {name}", "x": 10, "y": 10},
                {"type": "input", "label": "Name", "x": 10, "y": 40},
                {"type": "textarea", "label": "Description", "x": 10, "y": 80},
                {"type": "button", "text": "Submit", "x": 10, "y": 150},
            ]
        if page_type == "dashboard":
            return [
                {
                    "type": "header",
                    "text": f"{name} Dashboard",
                    "x": 10,
                    "y": 10,
                },
                {"type": "chart_placeholder", "x": 10, "y": 40, "w": 100, "h": 60},
                {
                    "type": "stat_card",
                    "x": 120,
                    "y": 40,
                    "label": "Total",
                    "value": "--",
                },
            ]
        return [{"type": "header", "text": name, "x": 10, "y": 10}]

    def _layout_planner(self, pages: list[WireframePage]) -> None:
        cols = max(1, self.CANVAS_WIDTH // (self.PAGE_WIDTH + 40))
        for i, page in enumerate(pages):
            row, col = divmod(i, cols)
            page.x = 20 + col * (self.PAGE_WIDTH + 40)
            page.y = 20 + row * (self.PAGE_HEIGHT + 60)
            page.width = self.PAGE_WIDTH
            page.height = self.PAGE_HEIGHT

    def _navigation_linker(self, pages: list[WireframePage]) -> list[NavigationEdge]:
        edges: list[NavigationEdge] = []
        list_pages = {p.entity_id: p for p in pages if p.page_type == "list"}
        detail_pages = {p.entity_id: p for p in pages if p.page_type == "detail"}
        form_pages = {p.entity_id: p for p in pages if p.page_type == "form"}
        for eid, lp in list_pages.items():
            if eid in detail_pages:
                edges.append(
                    NavigationEdge(lp.page_id, detail_pages[eid].page_id, "view", 1.0)
                )
            if eid in form_pages:
                edges.append(
                    NavigationEdge(lp.page_id, form_pages[eid].page_id, "create", 0.8)
                )
        return edges

    def _render_svg(
        self, pages: list[WireframePage], edges: list[NavigationEdge]
    ) -> str:
        c = self.CANVAS_WIDTH
        h = self.CANVAS_HEIGHT
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{c}" '
            f'height="{h}" viewBox="0 0 {c} {h}">',
            '<rect width="100%" height="100%" fill="#f5f5f5"/>',
        ]
        for page in pages:
            parts.extend(self._render_page_svg(page))
        for edge in edges:
            src = next((p for p in pages if p.page_id == edge.source), None)
            dst = next((p for p in pages if p.page_id == edge.target), None)
            if src and dst:
                parts.append(
                    f'<line x1="{src.x + src.width / 2}" '
                    f'y1="{src.y + src.height}" '
                    f'x2="{dst.x + dst.width / 2}" y2="{dst.y}" '
                    f'stroke="#666" stroke-width="2" '
                    'marker-end="url(#arrowhead)"/>'
                )
        parts.append(
            '<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" '
            'refX="9" refY="3.5" orient="auto">'
            '<polygon points="0 0, 10 3.5, 0 7" fill="#666"/>'
            '</marker></defs>'
        )
        parts.append("</svg>")
        return "\n".join(parts)

    def _render_page_svg(self, page: WireframePage) -> list[str]:
        parts: list[str] = []
        x, y, w, h = page.x, page.y, page.width, page.height
        tc = _COLORS["types"].get(page.page_type, "#f5f5f5")
        parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="{_COLORS["bg"]}" stroke="{_COLORS["border"]}" '
            'stroke-width="2" rx="4"/>'
        )
        parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="24" '
            f'fill="{_COLORS["header"]}" stroke="{_COLORS["border"]}" '
            'stroke-width="1" rx="4"/>'
        )
        parts.append(
            f'<text x="{x + 8}" y="{y + 17}" font-size="12" '
            f'font-weight="bold" fill="#1565c0">{page.title}</text>'
        )
        parts.append(
            f'<rect x="{x + 1}" y="{y + 24}" width="{w - 2}" '
            f'height="{h - 25}" fill="{tc}"/>'
        )
        for elem in page.elements:
            ex = x + elem.get("x", 10)
            ey = y + 30 + elem.get("y", 0)
            if elem["type"] == "search_bar":
                parts.append(
                    f'<rect x="{ex}" y="{ey}" width="200" height="20" '
                    'fill="white" stroke="#999" rx="2"/>'
                )
            elif elem["type"] == "table":
                for row in range(elem.get("rows", 3)):
                    parts.append(
                        f'<rect x="{ex}" y="{ey + row * 20}" width="200" '
                        'height="18" fill="white" stroke="#ddd"/>'
                    )
            elif elem["type"] == "button":
                parts.append(
                    f'<rect x="{ex}" y="{ey}" width="60" height="22" '
                    f'fill="{_COLORS["accent"]}" rx="2"/>'
                )
                parts.append(
                    f'<text x="{ex + 12}" y="{ey + 15}" font-size="10" '
                    f'fill="white">{elem["text"]}</text>'
                )
            elif elem["type"] == "input":
                parts.append(
                    f'<text x="{ex}" y="{ey}" font-size="9" '
                    f'fill="#666">{elem.get("label", "")}</text>'
                )
                parts.append(
                    f'<rect x="{ex}" y="{ey + 2}" width="200" height="18" '
                    'fill="white" stroke="#999" rx="2"/>'
                )
        return parts
