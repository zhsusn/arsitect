"""PageSpecResolver — Parse detailed-requirement module-requirements.md into structured page specs.

Extracts:
- Page manifest (§2.1)
- Field definitions (§3.1)
- Interaction specs / nav targets (§5.1)
- Mermaid nav graph (§2.4 / §5.2)
"""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class FieldSpec:
    """A field definition from the IO table."""

    name: str
    page_ref: str = ""  # e.g. "新建项目-步骤①"
    field_type: str = "text"
    required: bool = False
    validation: str = ""
    example: str = ""


@dataclass
class ButtonSpec:
    """An interactive element / button from interaction spec."""

    label: str
    element_id: str = ""
    trigger: str = "click"
    preconditions: str = ""
    success_result: str = ""
    target_page: str = ""  # parsed from success_result / nav targets


@dataclass
class PageSpec:
    """Structured specification for a single page."""

    page_name: str
    page_id: str = ""  # e.g. Pg_Dashboard from Mermaid
    url_route: str = ""
    page_type: str = "FORM"
    description: str = ""
    fields: list[FieldSpec] = field(default_factory=list)
    buttons: list[ButtonSpec] = field(default_factory=list)
    nav_targets: list[str] = field(default_factory=list)  # outgoing page names
    incoming_from: list[str] = field(default_factory=list)  # incoming page names


@dataclass
class NavEdge:
    """Directed edge in the navigation graph."""

    source: str
    target: str
    label: str = ""
    style: str = "solid"  # solid or dashed


@dataclass
class ModuleSpec:
    """Complete parsed spec for one module-requirements.md."""

    module_id: str = ""
    module_name: str = ""
    related_stories: list[str] = field(default_factory=list)
    md_path: str = ""
    pages: list[PageSpec] = field(default_factory=list)
    nav_edges: list[NavEdge] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

_SECTION_RE = re.compile(r"^(#{2,3})\s+(.*)$", re.MULTILINE)
_TABLE_ROW_RE = re.compile(r"^\|(.+)\|$", re.MULTILINE)
_MERMAID_BLOCK_RE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)

# Header metadata patterns
_MODULE_ID_RE = re.compile(
    r"[\*\-]?\s*\*\*模块编号\*\*\s*[:：]\s*(.+?)(?:\s*$|\s+\*\*)", re.MULTILINE
)
_MODULE_NAME_RE = re.compile(
    r"[\*\-]?\s*\*\*模块名称\*\*\s*[:：]\s*(.+?)(?:\s*$|\s+\*\*)", re.MULTILINE
)
_RELATED_STORIES_RE = re.compile(
    r"[\*\-]?\s*\*\*关联用户故事\*\*\s*[:：]\s*(.+?)(?:\s*$|\s+\*\*)", re.MULTILINE
)


# ---------------------------------------------------------------------------
# Markdown table parser
# ---------------------------------------------------------------------------


def _parse_markdown_table(block: str) -> list[dict[str, str]]:
    """Parse a markdown table into list of row-dicts."""
    rows_raw: list[str] = []
    for line in block.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("|") and "---" in line:
            continue
        if line.startswith("|") and line.endswith("|"):
            rows_raw.append(line)

    if not rows_raw:
        return []

    # First row is header
    header = [c.strip() for c in rows_raw[0].strip("|").split("|")]
    results: list[dict[str, str]] = []
    for row in rows_raw[1:]:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        row_dict = {}
        for i, h in enumerate(header):
            # Normalise header names
            key = h.replace(" ", "_").lower()
            row_dict[key] = cells[i] if i < len(cells) else ""
        results.append(row_dict)
    return results


def _extract_section(content: str, *title_keywords: str) -> str:
    """Extract content block under a section whose title contains any keyword."""
    lines = content.splitlines()
    capture = False
    depth = 0
    buffer: list[str] = []

    for line in lines:
        sec_match = _SECTION_RE.match(line)
        if sec_match:
            hashes, title = sec_match.groups()
            current_depth = len(hashes)
            if not capture:
                if any(kw in title for kw in title_keywords):
                    capture = True
                    depth = current_depth
                    buffer = []
            else:
                if current_depth <= depth:
                    break
        if capture:
            buffer.append(line)

    return "\n".join(buffer)


def _extract_all_sections(content: str, *title_keywords: str) -> list[str]:
    """Extract all sibling sections matching keywords (e.g. all ### 5.x)."""
    lines = content.splitlines()
    blocks: list[list[str]] = []
    capture = False
    depth = 0
    buffer: list[str] = []

    for line in lines:
        sec_match = _SECTION_RE.match(line)
        if sec_match:
            hashes, title = sec_match.groups()
            current_depth = len(hashes)
            if not capture:
                if any(kw in title for kw in title_keywords):
                    capture = True
                    depth = current_depth
                    buffer = [line]
            else:
                if current_depth <= depth:
                    if any(kw in title for kw in title_keywords):
                        blocks.append(buffer)
                        buffer = [line]
                    else:
                        blocks.append(buffer)
                        capture = False
                        buffer = []
                else:
                    buffer.append(line)
        else:
            if capture:
                buffer.append(line)

    if capture and buffer:
        blocks.append(buffer)

    return ["\n".join(b) for b in blocks]


# ---------------------------------------------------------------------------
# Page type inference
# ---------------------------------------------------------------------------

_PAGE_TYPE_KEYWORDS: dict[str, list[str]] = {
    "LIST": ["列表", "查询", "搜索", "筛选", "分页", "批量", "table", "list"],
    "DETAIL": ["详情", "查看", "明细", "信息展示", "面板", "profile", "detail"],
    "DASHBOARD": [
        "仪表盘",
        "统计",
        "指标",
        "图表",
        "概览",
        "工作台",
        "看板",
        "总览页",
        "首页",
        "dashboard",
        "chart",
        "homepage",
    ],
    "FORM": ["表单", "填写", "提交", "编辑", "创建", "form", "input"],
    "MODAL": ["弹窗", "弹层", "对话框", "modal", "dialog", "浮层", "侧滑", "抽屉", "drawer"],
    "SEARCH": ["搜索", "检索", "查找", "search", "filter"],
    "WIZARD": ["向导", "步骤", "流程", "分步", "wizard", "step"],
}


def _infer_page_type(page_name: str, description: str = "") -> str:
    """Infer page type from name + description, title-weighted."""
    title_lower = page_name.lower()
    desc_lower = description.lower()
    scores: dict[str, int] = {}
    for pt, keywords in _PAGE_TYPE_KEYWORDS.items():
        title_score = 0
        desc_score = 0
        for kw in keywords:
            if kw.isascii():
                pattern = re.compile(rf"\b{re.escape(kw)}\b")
                title_score += len(pattern.findall(title_lower))
                desc_score += len(pattern.findall(desc_lower))
            else:
                title_score += title_lower.count(kw)
                desc_score += desc_lower.count(kw)
        total = title_score * 5 + desc_score
        if total:
            scores[pt] = total
    if not scores:
        return "FORM"
    return max(scores, key=lambda k: scores[k])


# ---------------------------------------------------------------------------
# Mermaid flowchart parser
# ---------------------------------------------------------------------------


def _parse_mermaid_flowchart(mermaid_text: str) -> tuple[list[str], list[NavEdge]]:
    """Parse mermaid flowchart LR into nodes and edges.

    Returns:
        (node_labels, edges) where node_labels are human-readable page names.
    """
    nodes: dict[str, str] = {}  # id -> label
    edges: list[NavEdge] = []

    for line in mermaid_text.splitlines():
        line = line.strip()
        if not line or line.startswith("subgraph") or line.startswith("end"):
            continue

        # Node definitions: Pg_XXX["label"]
        node_match = re.findall(r'(Pg_\w+)\[(?:\s*"([^"]+)"\s*)\]', line)
        for nid, label in node_match:
            # label may contain <br> tags — strip them
            clean = re.sub(r"<br\s*/?>", " ", label).strip()
            nodes[nid] = clean

        # Also handle node definitions with quotes but no brackets: Pg_XXX["label"]
        node_match2 = re.findall(r'(Pg_\w+)\["([^"]+)"\]', line)
        for nid, label in node_match2:
            clean = re.sub(r"<br\s*/?>", " ", label).strip()
            nodes[nid] = clean

        # Edge definitions: A["label"] -->|label| B["label"]  or A -.->|label| B
        edge_match = re.findall(
            r"(Pg_\w+)(?:\[[^\]]*\])?\s*(-\.->|-->)\s*\|([^|]*)\|\s*(Pg_\w+)(?:\[[^\]]*\])?",
            line,
        )
        for src, arrow, label, tgt in edge_match:
            edges.append(
                NavEdge(
                    source=nodes.get(src, src),
                    target=nodes.get(tgt, tgt),
                    label=label.strip('"')
                    if label.startswith('"') and label.endswith('"')
                    else label,
                    style="dashed" if "-.->" in arrow else "solid",
                )
            )

        # Edge without label: A["label"] --> B["label"]
        edge_match2 = re.findall(
            r"(Pg_\w+)(?:\[[^\]]*\])?\s*(-\.->|--)\s*(Pg_\w+)(?:\[[^\]]*\])?",
            line,
        )
        for src, arrow, tgt in edge_match2:
            edges.append(
                NavEdge(
                    source=nodes.get(src, src),
                    target=nodes.get(tgt, tgt),
                    label="",
                    style="dashed" if "-.->" in arrow else "solid",
                )
            )

    return list(nodes.values()), edges


# ---------------------------------------------------------------------------
# Main resolver
# ---------------------------------------------------------------------------


def parse_module_requirements(content: str, md_path: str = "") -> ModuleSpec:
    """Parse a single module-requirements.md into ModuleSpec."""
    spec = ModuleSpec(md_path=md_path)

    # 1. Header metadata
    m = _MODULE_ID_RE.search(content)
    if m:
        spec.module_id = m.group(1).strip()
    m = _MODULE_NAME_RE.search(content)
    if m:
        spec.module_name = m.group(1).strip()
    m = _RELATED_STORIES_RE.search(content)
    if m:
        raw = m.group(1).strip()
        # e.g. "US-001（创建与管理项目）" or "US-001, US-002"
        spec.related_stories = re.findall(r"US-\d+", raw)

    # 2. Page manifest (§2.1)
    page_manifest_block = _extract_section(content, "2.1", "页面清单")
    manifest_rows = _parse_markdown_table(page_manifest_block)

    page_map: dict[str, PageSpec] = {}
    for row in manifest_rows:
        name = row.get("页面名称", "").strip()
        url = row.get("url/入口", row.get("url/���", "")).strip()
        duty = row.get("职责", row.get("职责", "")).strip()
        if not name:
            continue
        ptype = _infer_page_type(name, duty)
        page = PageSpec(
            page_name=name,
            url_route=url,
            page_type=ptype,
            description=duty,
        )
        page_map[name] = page
        spec.pages.append(page)

    # 3. User input fields (§3.1) — attach to pages by page_ref
    fields_block = _extract_section(content, "3.1", "用户输入字段表")
    field_rows = _parse_markdown_table(fields_block)
    for row in field_rows:
        f = FieldSpec(
            name=row.get("字段名", "").strip(),
            page_ref=row.get("所属页面/步骤", "").strip(),
            field_type=row.get("类型", "text").strip(),
            required=row.get("必填", "").strip() in ("是", "Y", "Yes", "true"),
            validation=row.get("校验规则", "").strip(),
            example=row.get("示例值", "").strip(),
        )
        # Attach to best-matching page
        _attach_field_to_page(page_map, f)

    # 4. Interaction spec (§5.1) — extract buttons & nav targets
    interaction_sections = _extract_all_sections(content, "5.1", "按钮级交互状态机")
    for sec in interaction_sections:
        # Each section may contain multiple pages ("#### 页面：..." or "##### 元素：...")
        _parse_interaction_section(page_map, sec)

    # 5. Mermaid nav graphs (§2.4 and §5.2)
    nav_blocks = _extract_section(content, "2.4", "页面跳转图")
    nav_blocks += "\n" + _extract_section(content, "5.2", "页面间跳转关系图")
    mermaid_blocks = _MERMAID_BLOCK_RE.findall(nav_blocks)
    all_nodes: set[str] = set()
    for mb in mermaid_blocks:
        nodes, edges = _parse_mermaid_flowchart(mb)
        all_nodes.update(nodes)
        spec.nav_edges.extend(edges)

    # 6. Build incoming edges map & page_id mapping from Mermaid
    incoming: dict[str, list[str]] = {}
    page_id_map: dict[str, str] = {}
    for edge in spec.nav_edges:
        incoming.setdefault(edge.target, []).append(edge.source)
        # Try to map Mermaid node label -> PageSpec.page_name
        for pg in spec.pages:
            if edge.source in pg.page_name or pg.page_name in edge.source:
                page_id_map[pg.page_name] = edge.source
            if edge.target in pg.page_name or pg.page_name in edge.target:
                page_id_map[pg.page_name] = edge.target

    for pg in spec.pages:
        pg.nav_targets = [
            e.target for e in spec.nav_edges if e.source in pg.page_name or pg.page_name in e.source
        ]
        pg.incoming_from = incoming.get(pg.page_name, [])
        if pg.page_name in page_id_map:
            pg.page_id = page_id_map[pg.page_name]

    return spec


def _attach_field_to_page(page_map: dict[str, PageSpec], field: FieldSpec) -> None:
    """Attach a field to the best-matching page based on page_ref."""
    if not field.page_ref:
        # Fallback: attach to first page
        if page_map:
            next(iter(page_map.values())).fields.append(field)
        return

    ref = field.page_ref.lower()
    best_match: PageSpec | None = None
    best_score = 0
    for name, page in page_map.items():
        score = 0
        # Exact match or substring match
        if name.lower() in ref or ref in name.lower():
            score = 10
        # Keyword match
        for kw in ref.split("-"):
            kw = kw.strip()
            if kw and kw in name.lower():
                score += 1
        if score > best_score:
            best_score = score
            best_match = page

    if best_match:
        best_match.fields.append(field)
    elif page_map:
        next(iter(page_map.values())).fields.append(field)


def _parse_interaction_section(page_map: dict[str, PageSpec], section_text: str) -> None:
    """Parse interaction spec section to extract buttons and nav targets."""
    # Find current page context from "#### 页面：..." headers
    current_page: PageSpec | None = None
    for line in section_text.splitlines():
        page_match = re.search(r"#{3,4}\s*页面[：:]\s*(.+?)(?:\s*\(|$)", line)
        if page_match:
            page_name = page_match.group(1).strip()
            # Find matching PageSpec
            for pg in page_map.values():
                if page_name in pg.page_name or pg.page_name in page_name:
                    current_page = pg
                    break

        # Element header: "##### 元素：...按钮（#id）"
        elem_match = re.search(r"#{4,5}\s*元素[：:]\s*(.+?)(?:\s*\(|$)", line)
        if elem_match and current_page:
            elem_text = elem_match.group(1).strip()
            # Extract button label
            label = elem_text.split("（")[0].strip()
            elem_id = ""
            id_match = re.search(r"#(\w+)", elem_text)
            if id_match:
                elem_id = id_match.group(1)

            # Look for success_result / target_page in the following table
            # We parse the whole section as tables and look for rows after this header
            # Simplification: scan for "成功结果" or "立即反馈" rows
            btn = ButtonSpec(label=label, element_id=elem_id)
            current_page.buttons.append(btn)

    # Second pass: parse tables for nav targets (success_result contains page names)
    tables = _parse_markdown_table(section_text)
    for row in tables:
        val = row.get("说明", "")
        if not val:
            continue
        # Look for page references like "Pg_XXX" or Chinese page names
        nav_mentions = re.findall(
            r"(?:跳转至|打开|进入|返回|关闭|导航至)([^，,。.；;\n]{1,15})", val
        )
        for mention in nav_mentions:
            mention = mention.strip()
            if mention and current_page and mention not in current_page.nav_targets:
                current_page.nav_targets.append(mention)


# ---------------------------------------------------------------------------
# Batch resolver for a project
# ---------------------------------------------------------------------------


def scan_module_requirements(base_path: pathlib.Path) -> list[pathlib.Path]:
    """Scan openspec for all module-requirements.md files."""
    pattern = "openspec/changes/*/detailed-requirements/**/module-requirements.md"
    candidates = list(base_path.glob(pattern))
    if not candidates:
        # Fallback: try project root
        candidates = list(pathlib.Path(__file__).resolve().parents[3].glob(pattern))
    return candidates


def resolve_project_specs(base_path: pathlib.Path) -> list[ModuleSpec]:
    """Resolve all module specs for a project directory."""
    specs: list[ModuleSpec] = []
    for md_path in scan_module_requirements(base_path):
        try:
            content = md_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            content = md_path.read_text(encoding="gbk")
        except Exception:
            continue
        spec = parse_module_requirements(content, str(md_path))
        if spec.pages:
            specs.append(spec)
    return specs


# ---------------------------------------------------------------------------
# Flatten to simple dicts for sketch_generator consumption
# ---------------------------------------------------------------------------


def flatten_specs_to_pages(specs: list[ModuleSpec]) -> list[dict[str, Any]]:
    """Flatten ModuleSpec list into page dicts compatible with sketch_generator."""
    results: list[dict[str, Any]] = []
    for mod in specs:
        for pg in mod.pages:
            results.append(
                {
                    "page_name": pg.page_name,
                    "page_type": pg.page_type,
                    "page_id": pg.page_id,
                    "url_route": pg.url_route,
                    "description": pg.description,
                    "module_id": mod.module_id,
                    "module_name": mod.module_name,
                    "fields": [
                        {
                            "name": f.name,
                            "type": f.field_type,
                            "required": f.required,
                            "validation": f.validation,
                        }
                        for f in pg.fields
                    ],
                    "buttons": [
                        {
                            "label": b.label,
                            "element_id": b.element_id,
                            "trigger": b.trigger,
                            "target_page": b.target_page,
                        }
                        for b in pg.buttons
                    ],
                    "nav_targets": pg.nav_targets,
                    "incoming_from": pg.incoming_from,
                    "source_md_path": mod.md_path,
                }
            )
    return results


def build_nav_graph(specs: list[ModuleSpec]) -> dict[str, Any]:
    """Build a global navigation graph from all module specs."""
    nodes: set[str] = set()
    edges: list[dict[str, str]] = []
    for mod in specs:
        for pg in mod.pages:
            nodes.add(pg.page_name)
        for e in mod.nav_edges:
            edges.append(
                {
                    "source": e.source,
                    "target": e.target,
                    "label": e.label,
                    "style": e.style,
                }
            )
    return {
        "nodes": sorted(nodes),
        "edges": edges,
    }
