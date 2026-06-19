"""SketchGenerator — HTML navigable sketch from PageSpecs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.docforge.fragment_registry import FragmentRegistry


@dataclass
class PageSpec:
    """Parsed page specification."""

    page_id: str
    page_type: str
    entity_id: str
    title: str
    fields: list[dict[str, Any]]
    actions: list[str]


class SketchGenerator:
    """Generate navigable HTML wireframe sketch."""

    COLORS: dict[str, str] = {
        "bg": "#e8e8e8",
        "page_bg": "#ffffff",
        "border": "#999999",
        "header_bg": "#d0d0d0",
        "element_bg": "#f0f0f0",
        "text": "#333333",
        "label": "#666666",
        "accent": "#4a90d9",
    }

    def __init__(self, fragment_registry: FragmentRegistry) -> None:
        self.fragments = fragment_registry

    async def generate(self, project_id: str) -> str:
        pagespecs = await self.fragments.get_pagespecs(project_id)
        if not pagespecs:
            return self._empty_page()
        pages = [self._parse_pagespec(p) for p in pagespecs]
        return self._render_html(pages)

    def _parse_pagespec(self, data: dict[str, Any]) -> PageSpec:
        return PageSpec(
            page_id=data.get("page_id", "unknown"),
            page_type=data.get("page_type", "list"),
            entity_id=data.get("entity_id", ""),
            title=data.get("title", "Untitled"),
            fields=data.get("fields", []),
            actions=data.get("actions", []),
        )

    def _render_html(self, pages: list[PageSpec]) -> str:
        c = self.COLORS
        n = len(pages)
        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Wireframe Sketch - {n} pages</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
background:{c["bg"]};padding:20px}}
.sketch-page{{background:{c["page_bg"]};border:2px solid {c["border"]};
margin-bottom:20px;max-width:900px}}
.sketch-header{{background:{c["header_bg"]};padding:12px 16px;
border-bottom:2px solid {c["border"]};display:flex;
justify-content:space-between;align-items:center}}
.sketch-header h2{{font-size:16px;color:{c["text"]}}}
.type-badge{{background:{c["accent"]};color:white;font-size:11px;
padding:2px 8px;border-radius:10px}}
.sketch-body{{padding:16px}}
.sketch-element{{background:{c["element_bg"]};border:1px dashed {c["border"]};
padding:8px 12px;margin-bottom:8px;color:{c["label"]};font-size:13px}}
.sketch-table{{width:100%;border-collapse:collapse;margin-top:8px}}
.sketch-table th,.sketch-table td{{border:1px solid {c["border"]};
padding:6px 8px;font-size:12px;color:{c["text"]}}}
.sketch-table th{{background:{c["header_bg"]};font-weight:600}}
.sketch-btn{{display:inline-block;background:{c["accent"]};color:white;
padding:6px 16px;font-size:12px;border:none;margin-right:8px;margin-top:8px}}
.sketch-input{{width:100%;padding:6px;border:1px solid {c["border"]};
background:white;margin-top:4px;font-size:12px;color:{c["label"]}}}
.field-label{{font-size:11px;color:{c["label"]};margin-top:8px}}
.page-nav{{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}}
.page-nav a{{padding:6px 12px;background:white;border:1px solid {c["border"]};
text-decoration:none;color:{c["text"]};font-size:12px}}
.page-nav a:hover{{background:{c["accent"]};color:white}}
</style></head><body>
<h1 style="font-size:18px;margin-bottom:16px;color:{c["text"]}">
Wireframe Sketch <span style="font-size:13px;font-weight:normal;
color:{c["label"]}">({n} pages)</span></h1>
<div class="page-nav">"""
        for page in pages:
            html += f'<a href="#{page.page_id}">{page.title}</a>\n'
        html += "</div>\n"
        for page in pages:
            html += self._render_page(page)
        html += "</body></html>"
        return html

    def _render_page(self, page: PageSpec) -> str:
        html = (
            f'<div class="sketch-page" id="{page.page_id}">\n'
            f'<div class="sketch-header"><h2>{page.title}</h2>'
            f'<span class="type-badge">{page.page_type.upper()}</span></div>\n'
            '<div class="sketch-body">'
        )
        render_fn = {
            "list": self._render_list,
            "detail": self._render_detail,
            "form": self._render_form,
            "dashboard": self._render_dashboard,
            "search": self._render_search,
        }.get(page.page_type, self._render_list)
        html += render_fn(page)
        for action in page.actions:
            html += f'<button class="sketch-btn">{action}</button>\n'
        html += "</div></div>\n"
        return html

    def _render_list(self, page: PageSpec) -> str:
        fields = page.fields or [{"name": "ID"}, {"name": "Name"}, {"name": "Status"}]
        html = '<div class="sketch-element">[Search Bar]  Search...</div>\n'
        html += '<table class="sketch-table"><tr>\n'
        for f in fields[:5]:
            html += f"<th>{f.get('name', '')}</th>\n"
        html += "<th>Actions</th></tr>\n"
        for _ in range(3):
            html += "<tr>\n"
            for _ in fields[:5]:
                html += '<td style="color:#aaa">---</td>\n'
            html += '<td><span style="color:#4a90d9">[View] [Edit]</span></td></tr>\n'
        html += '</table>\n<div class="sketch-element" style="margin-top:8px">'
        html += "[Pagination]  &lt; 1 2 3 &gt;</div>\n"
        return html

    def _render_detail(self, page: PageSpec) -> str:
        fields = page.fields or [{"name": "Name"}, {"name": "Description"}, {"name": "Status"}]
        html = ""
        for f in fields:
            html += f'<div class="field-label">{f.get("name", "")}</div>\n'
            html += f'<div class="sketch-element">{{{f.get("name", "value")}}}</div>\n'
        return html

    def _render_form(self, page: PageSpec) -> str:
        fields = page.fields or [{"name": "Name"}, {"name": "Description"}]
        html = ""
        for f in fields:
            html += f'<div class="field-label">{f.get("name", "")} *</div>\n'
            html += f'<input class="sketch-input" value="Enter {f.get("name", "")}...">\n'
        html += '<div style="margin-top:12px"><button class="sketch-btn">'
        html += "Submit</button>\n"
        html += '<button class="sketch-btn" style="background:#999">'
        html += "Cancel</button></div>\n"
        return html

    def _render_dashboard(self, page: PageSpec) -> str:
        html = (
            '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;'
            'gap:12px;margin-bottom:12px">\n'
        )
        for label in ["Total Users", "Active", "Revenue"]:
            html += (
                f'<div class="sketch-element" style="text-align:center">\n'
                f'<div style="font-size:11px;color:#666">{label}</div>\n'
                f'<div style="font-size:24px;font-weight:bold;color:#333;'
                f'margin-top:4px">---</div></div>\n'
            )
        html += "</div>\n"
        html += (
            '<div class="sketch-element" style="height:150px;'
            'display:flex;align-items:center;justify-content:center">'
            "[Chart Placeholder]</div>\n"
        )
        return html

    def _render_search(self, page: PageSpec) -> str:
        html = '<div style="display:flex;gap:8px;margin-bottom:12px">\n'
        html += '<input class="sketch-input" value="Search keywords..." '
        html += 'style="flex:1">\n'
        html += '<button class="sketch-btn">Search</button>\n'
        html += '<button class="sketch-btn" style="background:#666">'
        html += "Advanced</button></div>\n"
        html += '<div class="sketch-element">[Filter Panel] '
        html += "Status | Date | Category</div>\n"
        html += '<div class="sketch-element" style="margin-top:8px">'
        html += "[Results List]  10 results found</div>\n"
        return html

    def _empty_page(self) -> str:
        return """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>No Data</title></head>
<body style="font-family:sans-serif;padding:40px;color:#666">
<h2>No PageSpec found</h2>
<p>Add PageSpec to your PRD document metadata to generate sketch.</p>
<pre style="background:#f5f5f5;padding:16px">metadata:
  pagespecs:
    - page_id: user_list
      page_type: list
      title: User List
      fields:
        - { name: ID }
        - { name: Name }
        - { name: Email }</pre>
</body></html>"""
