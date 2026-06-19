"""SketchGenerator — PageSpec parser + SVG sketch renderer.

V2: Renders from structured PageSpec (extracted from module-requirements.md)
instead of sparse user_story text.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class PageField:
    """页面字段定义."""

    name: str
    field_type: str = "text"
    required: bool = False
    validation: str = ""


@dataclass
class PageButton:
    """页面按钮/操作定义."""

    label: str
    action: str = "click"
    target: str | None = None
    element_id: str = ""


@dataclass
class ParsedPage:
    """PageSpec 解析结果."""

    page_name: str
    page_type: str
    page_id: str = ""
    url_route: str = ""
    description: str = ""
    module_id: str = ""
    fields: list[PageField] = field(default_factory=list)
    buttons: list[PageButton] = field(default_factory=list)
    nav_targets: list[str] = field(default_factory=list)
    incoming_from: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# SVG Renderers (upgraded for real field data)
# ---------------------------------------------------------------------------


def _esc(text: str) -> str:
    """Escape XML special chars."""
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def _field_type_badge_color(field_type: str) -> str:
    """Return a color for field type badge."""
    colors: dict[str, str] = {
        "文本": "#0d6efd",
        "多行文本": "#0d6efd",
        "text": "#0d6efd",
        "单选": "#198754",
        "多选": "#198754",
        "选择": "#198754",
        "select": "#198754",
        "整数": "#fd7e14",
        "数字": "#fd7e14",
        "number": "#fd7e14",
        "时间": "#6f42c1",
        "日期": "#6f42c1",
        "date": "#6f42c1",
        "对象": "#dc3545",
        "数组": "#dc3545",
    }
    return colors.get(field_type, "#6c757d")


def _render_svg_form(page: ParsedPage) -> str:
    """渲染表单类型 SVG 草图（基于真实字段定义）."""
    field_h = 40
    btn_h = 44
    padding = 20
    header_h = 56
    w = 440
    h = header_h + len(page.fields) * field_h + len(page.buttons) * btn_h + padding * 4
    h = max(h, 200)

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>',
        f'<text x="{padding}" y="36" font-size="17" font-weight="bold" fill="#212529">{_esc(page.page_name)}</text>',
    ]
    # URL badge
    if page.url_route:
        lines.append(
            f'<text x="{w - padding}" y="36" font-size="10" text-anchor="end" fill="#868e96">'
            f"{_esc(page.url_route)}</text>"
        )

    y = header_h + padding
    for f in page.fields:
        # Field label
        label = f.name + (" *" if f.required else "")
        lines.append(
            f'<text x="{padding}" y="{y + 14}" font-size="12" fill="#495057">{_esc(label)}</text>'
        )
        # Type badge
        badge_color = _field_type_badge_color(f.field_type)
        lines.append(
            f'<rect x="{padding + 80}" y="{y + 2}" width="{min(60, len(f.field_type) * 10 + 8)}" '
            f'height="14" fill="{badge_color}" rx="3" opacity="0.15"/>'
        )
        lines.append(
            f'<text x="{padding + 84}" y="{y + 13}" font-size="9" fill="{badge_color}">'
            f"{_esc(f.field_type[:6])}</text>"
        )
        # Input box
        lines.append(
            f'<rect x="{padding}" y="{y + 18}" width="{w - padding * 2}" height="28" '
            f'fill="#fff" stroke="#adb5bd" stroke-dasharray="4 2" rx="3"/>'
        )
        # Validation hint
        if f.validation:
            hint = f.validation[:30] + "..." if len(f.validation) > 30 else f.validation
            lines.append(
                f'<text x="{padding + 4}" y="{y + 36}" font-size="9" fill="#dc3545">'
                f"{_esc(hint)}</text>"
            )
        y += field_h

    y += padding
    for b in page.buttons:
        bw = max(90, len(b.label) * 14 + 24)
        lines.append(
            f'<rect x="{padding}" y="{y}" width="{bw}" height="36" '
            f'fill="#e9ecef" stroke="#495057" rx="5"/>'
        )
        lines.append(
            f'<text x="{padding + bw // 2}" y="{y + 24}" font-size="14" '
            f'text-anchor="middle" fill="#212529">{_esc(b.label)}</text>'
        )
        if b.target:
            lines.append(
                f'<text x="{padding + bw + 8}" y="{y + 24}" font-size="10" fill="#0d6efd">'
                f"→ {_esc(b.target[:15])}</text>"
            )
        y += btn_h

    # Nav targets footer
    if page.nav_targets:
        nav_text = "跳转: " + ", ".join(page.nav_targets[:3])
        lines.append(
            f'<text x="{padding}" y="{h - 10}" font-size="10" fill="#0d6efd">{_esc(nav_text)}</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def _render_svg_list(page: ParsedPage) -> str:
    """渲染列表类型 SVG 草图."""
    padding = 20
    header_h = 56
    row_h = 38
    w = 560
    rows = max(3, len(page.fields))
    h = header_h + row_h * (rows + 1) + padding * 4

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>',
        f'<text x="{padding}" y="36" font-size="17" font-weight="bold" fill="#212529">{_esc(page.page_name)}</text>',
    ]

    # Search bar
    y = header_h + padding
    lines.append(
        f'<rect x="{padding}" y="{y}" width="{w - padding * 2 - 100}" height="32" '
        f'fill="#fff" stroke="#adb5bd" rx="3"/>'
    )
    lines.append(
        f'<text x="{padding + 8}" y="{y + 22}" font-size="12" fill="#adb5bd">搜索...</text>'
    )
    lines.append(
        f'<rect x="{w - padding - 90}" y="{y}" width="80" height="32" '
        f'fill="#e9ecef" stroke="#495057" rx="4"/>'
    )
    lines.append(
        f'<text x="{w - padding - 50}" y="{y + 22}" font-size="13" text-anchor="middle" '
        f'fill="#212529">搜索</text>'
    )

    y += 48
    # Table header
    lines.append(
        f'<rect x="{padding}" y="{y}" width="{w - padding * 2}" height="{row_h}" '
        f'fill="#e9ecef" stroke="#adb5bd" rx="2"/>'
    )
    cols = page.fields if page.fields else [PageField(name=f"列{i + 1}") for i in range(3)]
    col_w = (w - padding * 2) // max(1, len(cols))
    for i, f in enumerate(cols):
        cx = padding + col_w * i + col_w // 2
        label = f.name + (" *" if f.required else "")
        lines.append(
            f'<text x="{cx}" y="{y + 25}" font-size="12" text-anchor="middle" '
            f'fill="#495057">{_esc(label)}</text>'
        )
    y += row_h

    for _ in range(rows):
        lines.append(
            f'<rect x="{padding}" y="{y}" width="{w - padding * 2}" height="{row_h}" '
            f'fill="#fff" stroke="#dee2e6" rx="2"/>'
        )
        for i in range(len(cols)):
            cx = padding + col_w * i + col_w // 2
            lines.append(
                f'<text x="{cx}" y="{y + 25}" font-size="12" text-anchor="middle" '
                f'fill="#adb5bd">---</text>'
            )
        y += row_h

    # Pagination
    y += 10
    lines.append(
        f'<rect x="{w // 2 - 50}" y="{y}" width="100" height="22" '
        f'fill="none" stroke="#adb5bd" stroke-dasharray="3 3" rx="3"/>'
    )
    lines.append(
        f'<text x="{w // 2}" y="{y + 16}" font-size="11" text-anchor="middle" '
        f'fill="#adb5bd">分页器</text>'
    )

    lines.append("</svg>")
    return "\n".join(lines)


def _render_svg_dashboard(page: ParsedPage) -> str:
    """渲染仪表盘类型 SVG 草图."""
    padding = 20
    header_h = 56
    w = 560
    h = 380

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>',
        f'<text x="{padding}" y="36" font-size="17" font-weight="bold" fill="#212529">{_esc(page.page_name)}</text>',
    ]

    cards = [
        (padding, header_h + padding, (w - padding * 3) // 2, 110),
        (
            padding + (w - padding * 3) // 2 + padding,
            header_h + padding,
            (w - padding * 3) // 2,
            110,
        ),
        (padding, header_h + padding + 130, (w - padding * 3) // 2, 110),
        (
            padding + (w - padding * 3) // 2 + padding,
            header_h + padding + 130,
            (w - padding * 3) // 2,
            110,
        ),
    ]

    for i, (cx, cy, cw, ch) in enumerate(cards):
        lines.append(
            f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" '
            f'fill="#fff" stroke="#adb5bd" rx="6"/>'
        )
        label = page.fields[i].name if i < len(page.fields) else f"指标{i + 1}"
        lines.append(
            f'<text x="{cx + 12}" y="{cy + 26}" font-size="13" fill="#6c757d">{_esc(label)}</text>'
        )
        lines.append(f'<text x="{cx + 12}" y="{cy + 66}" font-size="28" fill="#495057">--</text>')
        # Mini chart placeholder
        lines.append(
            f'<rect x="{cx + cw - 80}" y="{cy + 30}" width="60" height="40" '
            f'fill="none" stroke="#dee2e6" stroke-dasharray="2 2" rx="3"/>'
        )

    # Bottom action bar
    if page.buttons:
        y = h - 50
        for b in page.buttons:
            bw = max(80, len(b.label) * 12 + 16)
            lines.append(
                f'<rect x="{padding}" y="{y}" width="{bw}" height="32" '
                f'fill="#e9ecef" stroke="#495057" rx="4"/>'
            )
            lines.append(
                f'<text x="{padding + bw // 2}" y="{y + 22}" font-size="13" '
                f'text-anchor="middle" fill="#212529">{_esc(b.label)}</text>'
            )
            padding += bw + 12

    lines.append("</svg>")
    return "\n".join(lines)


def _render_svg_detail(page: ParsedPage) -> str:
    """渲染详情类型 SVG 草图."""
    field_h = 36
    padding = 20
    header_h = 56
    w = 440
    h = header_h + len(page.fields) * field_h + padding * 4
    h = max(h, 180)

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>',
        f'<text x="{padding}" y="36" font-size="17" font-weight="bold" fill="#212529">{_esc(page.page_name)}</text>',
    ]

    y = header_h + padding
    for f in page.fields:
        lines.append(
            f'<text x="{padding}" y="{y + 20}" font-size="12" fill="#868e96">{_esc(f.name)}</text>'
        )
        lines.append(
            f'<rect x="{padding + 90}" y="{y}" width="{w - padding * 2 - 90}" height="26" '
            f'fill="#fff" stroke="#adb5bd" stroke-dasharray="3 3" rx="3"/>'
        )
        if f.field_type != "文本":
            badge_color = _field_type_badge_color(f.field_type)
            lines.append(
                f'<text x="{w - padding - 40}" y="{y + 20}" font-size="9" fill="{badge_color}">'
                f"{_esc(f.field_type[:6])}</text>"
            )
        y += field_h

    lines.append("</svg>")
    return "\n".join(lines)


def _render_svg_search(page: ParsedPage) -> str:
    """渲染搜索类型 SVG 草图."""
    padding = 20
    header_h = 56
    w = 560
    h = 280

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>',
        f'<text x="{padding}" y="36" font-size="17" font-weight="bold" fill="#212529">{_esc(page.page_name)}</text>',
    ]

    y = header_h + padding
    # Search bar
    lines.append(
        f'<rect x="{padding}" y="{y}" width="{w - padding * 2 - 90}" height="34" '
        f'fill="#fff" stroke="#adb5bd" rx="4"/>'
    )
    lines.append(
        f'<text x="{padding + 10}" y="{y + 23}" font-size="13" fill="#adb5bd">关键词...</text>'
    )
    lines.append(
        f'<rect x="{w - padding - 80}" y="{y}" width="80" height="34" '
        f'fill="#e9ecef" stroke="#495057" rx="4"/>'
    )
    lines.append(
        f'<text x="{w - padding - 40}" y="{y + 23}" font-size="13" text-anchor="middle" '
        f'fill="#212529">搜索</text>'
    )

    y += 60
    # Filter chips
    for i, f in enumerate(page.fields[:4]):
        chip_w = max(80, len(f.name) * 12 + 20)
        lines.append(
            f'<rect x="{padding + i * 110}" y="{y}" width="{chip_w}" height="30" '
            f'fill="#fff" stroke="#adb5bd" stroke-dasharray="3 3" rx="4"/>'
        )
        lines.append(
            f'<text x="{padding + i * 110 + chip_w // 2}" y="{y + 20}" font-size="11" '
            f'text-anchor="middle" fill="#6c757d">{_esc(f.name)}</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def _render_svg_modal(page: ParsedPage) -> str:
    """渲染弹窗类型 SVG 草图."""
    padding = 20
    w = 400
    h = 220
    cx = 40
    cy = 30

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<rect width="100%" height="100%" fill="rgba(0,0,0,0.06)"/>',
        f'<rect x="{cx}" y="{cy}" width="{w - cx * 2}" height="{h - cy * 2}" '
        f'fill="#fff" stroke="#495057" stroke-width="2" rx="8"/>',
        f'<text x="{cx + padding}" y="{cy + 32}" font-size="15" font-weight="bold" '
        f'fill="#212529">{_esc(page.page_name)}</text>',
    ]

    # Fields inside modal
    y = cy + 50
    for f in page.fields[:3]:
        lines.append(
            f'<text x="{cx + padding}" y="{y + 14}" font-size="11" fill="#6c757d">'
            f"{_esc(f.name)}{' *' if f.required else ''}</text>"
        )
        lines.append(
            f'<rect x="{cx + padding}" y="{y + 18}" width="{w - cx * 2 - padding * 2}" height="24" '
            f'fill="#fff" stroke="#adb5bd" stroke-dasharray="3 3" rx="3"/>'
        )
        y += 40

    # Buttons
    btn_y = h - cy - 40
    lines.append(
        f'<rect x="{w - cx - 90}" y="{btn_y}" width="70" height="30" '
        f'fill="#dc3545" stroke="#dc3545" rx="4" opacity="0.1"/>'
    )
    lines.append(
        f'<text x="{w - cx - 55}" y="{btn_y + 20}" font-size="12" text-anchor="middle" '
        f'fill="#dc3545">取消</text>'
    )
    lines.append(
        f'<rect x="{w - cx - 170}" y="{btn_y}" width="70" height="30" '
        f'fill="#0d6efd" stroke="#0d6efd" rx="4" opacity="0.1"/>'
    )
    lines.append(
        f'<text x="{w - cx - 135}" y="{btn_y + 20}" font-size="12" text-anchor="middle" '
        f'fill="#0d6efd">确认</text>'
    )

    lines.append("</svg>")
    return "\n".join(lines)


def _render_svg_wizard(page: ParsedPage) -> str:
    """渲染向导类型 SVG 草图."""
    padding = 20
    header_h = 56
    w = 480
    h = 320

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>',
        f'<text x="{padding}" y="36" font-size="17" font-weight="bold" fill="#212529">{_esc(page.page_name)}</text>',
    ]

    y = header_h + padding
    steps = ["步骤 1", "步骤 2", "步骤 3"]
    step_w = (w - padding * 2 - 40) // len(steps)
    for i, step in enumerate(steps):
        sx = padding + i * (step_w + 20)
        lines.append(
            f'<circle cx="{sx + 14}" cy="{y + 14}" r="14" fill="{"#0d6efd" if i == 0 else "#dee2e6"}"/>'
        )
        lines.append(
            f'<text x="{sx + 14}" y="{y + 19}" font-size="12" text-anchor="middle" '
            f'fill="{"#fff" if i == 0 else "#868e96"}">{i + 1}</text>'
        )
        lines.append(
            f'<text x="{sx + 14}" y="{y + 44}" font-size="11" text-anchor="middle" '
            f'fill="#495057">{_esc(step)}</text>'
        )
        if i < len(steps) - 1:
            lines.append(
                f'<line x1="{sx + 32}" y1="{y + 14}" x2="{sx + step_w + 2}" y2="{y + 14}" '
                f'stroke="#dee2e6" stroke-width="2"/>'
            )

    # Form area
    y += 70
    for f in page.fields[:2]:
        lines.append(
            f'<text x="{padding}" y="{y + 16}" font-size="12" fill="#6c757d">'
            f"{_esc(f.name)}{' *' if f.required else ''}</text>"
        )
        lines.append(
            f'<rect x="{padding}" y="{y + 20}" width="{w - padding * 2}" height="28" '
            f'fill="#fff" stroke="#adb5bd" stroke-dasharray="3 3" rx="3"/>'
        )
        y += 50

    lines.append("</svg>")
    return "\n".join(lines)


_RENDERERS: dict[str, Callable[..., str]] = {
    "FORM": _render_svg_form,
    "LIST": _render_svg_list,
    "DASHBOARD": _render_svg_dashboard,
    "DETAIL": _render_svg_detail,
    "SEARCH": _render_svg_search,
    "MODAL": _render_svg_modal,
    "WIZARD": _render_svg_wizard,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_page_svg(page: ParsedPage) -> str:
    """根据解析结果渲染对应类型的 SVG 草图."""
    renderer = _RENDERERS.get(page.page_type, _render_svg_form)
    return renderer(page)


def generate_sketch_from_module_specs(
    pages_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Batch generate sketch pages from structured PageSpec dicts.

    Args:
        pages_data: Output of page_spec_resolver.flatten_specs_to_pages().

    Returns:
        草图页面数据列表，每项可直接用于创建 SketchPage.
    """
    results: list[dict[str, Any]] = []
    for data in pages_data:
        fields = [
            PageField(
                name=f.get("name", ""),
                field_type=f.get("type", "text"),
                required=f.get("required", False),
                validation=f.get("validation", ""),
            )
            for f in data.get("fields", [])
        ]
        buttons = [
            PageButton(
                label=b.get("label", ""),
                action=b.get("trigger", "click"),
                target=b.get("target_page") or None,
                element_id=b.get("element_id", ""),
            )
            for b in data.get("buttons", [])
        ]
        page = ParsedPage(
            page_name=data.get("page_name", ""),
            page_type=data.get("page_type", "FORM"),
            page_id=data.get("page_id", ""),
            url_route=data.get("url_route", ""),
            description=data.get("description", ""),
            module_id=data.get("module_id", ""),
            fields=fields,
            buttons=buttons,
            nav_targets=data.get("nav_targets", []),
            incoming_from=data.get("incoming_from", []),
        )
        svg = render_page_svg(page)
        results.append(
            {
                "page_name": page.page_name,
                "page_type": page.page_type,
                "svg_content": svg,
                "fields_json": json.dumps(
                    [
                        {
                            "name": f.name,
                            "type": f.field_type,
                            "required": f.required,
                            "validation": f.validation,
                        }
                        for f in fields
                    ],
                    ensure_ascii=False,
                ),
                "buttons_json": json.dumps(
                    [
                        {
                            "label": b.label,
                            "action": b.action,
                            "target": b.target,
                            "element_id": b.element_id,
                        }
                        for b in buttons
                    ],
                    ensure_ascii=False,
                ),
                "nav_targets_json": json.dumps(page.nav_targets, ensure_ascii=False),
                "status": "GENERATED",
                "source_module_id": page.module_id,
                "source_md_path": data.get("source_md_path", ""),
            }
        )
    return results


# ---------------------------------------------------------------------------
# Legacy API (kept for backward compatibility)
# ---------------------------------------------------------------------------

# Re-export the old parse_user_story and generate_sketch_from_stories so
# existing tests that don't touch module specs continue to work.
# They are intentionally NOT updated; new code should use module-spec paths.


def _detect_page_type(title: str, desc: str | None) -> str:
    """Legacy page-type detection (kept for old API)."""
    import re as _re

    title_lower = title.lower()
    desc_lower = (desc or "").lower()
    scores: dict[str, int] = {}

    page_type_keywords: dict[str, list[str]] = {
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
        "MODAL": ["弹窗", "弹层", "对话框", "modal", "dialog"],
        "SEARCH": ["搜索", "检索", "查找", "search", "filter"],
        "WIZARD": ["向导", "步骤", "流程", "分步", "wizard", "step"],
    }

    for pt, keywords in page_type_keywords.items():
        title_score = 0
        desc_score = 0
        for kw in keywords:
            if kw.isascii():
                pattern = _re.compile(rf"\b{_re.escape(kw)}\b")
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


def _extract_fields(text: str) -> list[PageField]:
    """Legacy field extraction (kept for old API)."""
    import re as _re

    field_patterns = [
        _re.compile(r"[包括|含|有|需要|字段|输入]([^，,。.；;\n]{1,10})[输入框|字段|项|框]"),
        _re.compile(r"([^，,。.；;\n]{1,8})[：:]\s*输入"),
        _re.compile(r"输入([^，,。.；;\n]{1,8})"),
    ]
    fields: list[PageField] = []
    seen: set[str] = set()
    for pat in field_patterns:
        for m in pat.finditer(text):
            name = m.group(1).strip()
            if name and name not in seen and len(name) >= 2:
                seen.add(name)
                ftype = "text"
                if any(k in name for k in ["密码", "password", "密"]):
                    ftype = "password"
                elif any(k in name for k in ["日期", "时间", "date", "time"]):
                    ftype = "date"
                elif any(k in name for k in ["邮箱", "邮件", "email", "mail"]):
                    ftype = "email"
                elif any(k in name for k in ["手机", "电话", "tel", "phone"]):
                    ftype = "tel"
                elif any(k in name for k in ["选择", "下拉", "select"]):
                    ftype = "select"
                fields.append(PageField(name=name, field_type=ftype))
    if not fields:
        fields.append(PageField(name="字段1", field_type="text"))
        fields.append(PageField(name="字段2", field_type="text"))
    return fields


def _extract_buttons(text: str) -> list[PageButton]:
    """Legacy button extraction (kept for old API)."""
    import re as _re

    button_patterns = [
        _re.compile(r"[点击|按下|选择]([^，,。.；;\n]{1,8})[按钮|键]"),
        _re.compile(r"([^，,。.；;\n]{1,6})按钮"),
        _re.compile(r"(?:可以|能够|支持)([^，,。.；;\n]{1,8})(?:操作|功能)"),
    ]
    buttons: list[PageButton] = []
    seen: set[str] = set()
    for pat in button_patterns:
        for m in pat.finditer(text):
            label = m.group(1).strip()
            if label and label not in seen and len(label) >= 1:
                seen.add(label)
                buttons.append(PageButton(label=label))
    if not buttons:
        buttons.append(PageButton(label="提交"))
    return buttons


def _extract_nav_targets(text: str) -> list[str]:
    """Legacy nav target extraction (kept for old API)."""
    import re as _re

    nav_patterns = [
        _re.compile(r"跳转[至|到]([^，,。.；;\n]{1,10})"),
        _re.compile(r"进入([^，,。.；;\n]{1,10})"),
        _re.compile(r"前往([^，,。.；;\n]{1,10})"),
        _re.compile(r"[导向|链接|关联]至([^，,。.；;\n]{1,10})"),
    ]
    targets: list[str] = []
    seen: set[str] = set()
    for pat in nav_patterns:
        for m in pat.finditer(text):
            target = m.group(1).strip()
            if target and target not in seen and len(target) >= 2:
                seen.add(target)
                targets.append(target)
    return targets


def parse_user_story(story_title: str, story_desc: str | None) -> ParsedPage:
    """Legacy: parse single user story into page structure."""
    text = f"{story_title}\n{story_desc or ''}"
    page_type = _detect_page_type(story_title, story_desc)
    fields = _extract_fields(text)
    buttons = _extract_buttons(text)
    nav_targets = _extract_nav_targets(text)

    page_name = story_title.strip()
    if len(page_name) > 20:
        page_name = page_name[:20] + "..."

    return ParsedPage(
        page_name=page_name,
        page_type=page_type,
        fields=fields,
        buttons=buttons,
        nav_targets=nav_targets,
    )


def generate_sketch_from_stories(
    stories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Legacy: batch parse user stories and generate sketch page data."""
    results: list[dict[str, Any]] = []
    for s in stories:
        parsed = parse_user_story(s.get("title", ""), s.get("description"))
        svg = render_page_svg(parsed)
        results.append(
            {
                "page_name": parsed.page_name,
                "page_type": parsed.page_type,
                "svg_content": svg,
                "fields_json": json.dumps(
                    [
                        {"name": f.name, "type": f.field_type, "required": f.required}
                        for f in parsed.fields
                    ],
                    ensure_ascii=False,
                ),
                "buttons_json": json.dumps(
                    [
                        {"label": b.label, "action": b.action, "target": b.target}
                        for b in parsed.buttons
                    ],
                    ensure_ascii=False,
                ),
                "nav_targets_json": json.dumps(parsed.nav_targets, ensure_ascii=False),
                "status": "GENERATED",
            }
        )
    return results
