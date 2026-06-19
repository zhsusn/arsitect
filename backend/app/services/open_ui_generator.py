"""OpenUIGenerator — prompt assembler + local service client + HTML parser.

Based on DR-018 OpenUI Prototype Service.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import httpx

# Local OpenUI service endpoint (Docker)
DEFAULT_OPENUI_URL = "http://localhost:3000/api/generate"
DEFAULT_TIMEOUT = 15.0


class OpenUIServiceUnavailableError(Exception):
    """Raised when OpenUI local service is not reachable."""

    pass


def assemble_prompt(
    container_name: str,
    container_desc: str,
    endpoints: list[dict[str, Any]],
) -> str:
    """Assemble structured prompt for OpenUI service.

    Args:
        container_name: C4 Container name.
        container_desc: Container responsibility description.
        endpoints: List of interface contract endpoints.

    Returns:
        Natural language prompt text.
    """
    lines: list[str] = [
        "You are a UI generation assistant.",
        f"Generate a complete, interactive single-page HTML prototype for the '{container_name}' module.",
        f"Background: {container_desc}",
        "",
        "Endpoints:",
    ]
    for ep in endpoints:
        method = ep.get("method_type", "GET")
        path = ep.get("endpoint_path", "/")
        summary = ep.get("operation_summary", "")
        lines.append(f"- {method} {path}: {summary}")

    lines.extend(
        [
            "",
            "Requirements:",
            "- Use semantic HTML5, embedded CSS (Tailwind-like utility classes preferred), and vanilla JS.",
            "- Include navigation, data tables or forms based on endpoint semantics.",
            "- Support responsive layout.",
            "- Output a complete standalone HTML file (no external dependencies except CDN).",
            "- Use Chinese UI labels where appropriate.",
        ]
    )
    return "\n".join(lines)


def compute_content_hash(html: str) -> str:
    """Compute SHA-256 hash of HTML content."""
    return hashlib.sha256(html.encode("utf-8")).hexdigest()[:16]


async def generate_html(
    prompt: str,
    base_url: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Call local OpenUI service to generate HTML prototype.

    Args:
        prompt: Structured prompt text.
        base_url: Optional custom OpenUI service URL.
        timeout: Request timeout in seconds.

    Returns:
        Dict with html_content, generation_duration_ms, content_hash.

    Raises:
        OpenUIServiceUnavailableError: If service is unreachable or times out.
    """
    url = base_url or DEFAULT_OPENUI_URL
    payload = {"prompt": prompt, "format": "html"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            html = data.get("html", data.get("html_content", ""))
            if not html:
                raise OpenUIServiceUnavailableError("OpenUI returned empty HTML")
            return {
                "html_content": html,
                "generation_duration_ms": data.get("generation_duration_ms", 0),
                "content_hash": compute_content_hash(html),
            }
    except httpx.TimeoutException as exc:
        raise OpenUIServiceUnavailableError("OpenUI service call timed out") from exc
    except httpx.ConnectError as exc:
        raise OpenUIServiceUnavailableError("OpenUI service is unreachable") from exc
    except Exception as exc:
        raise OpenUIServiceUnavailableError(f"OpenUI call failed: {exc}") from exc


def split_pages(html_content: str) -> list[dict[str, str]]:
    """Split multi-page HTML into individual page segments.

    MVP implementation: if the HTML contains clear page separator comments,
    split by them; otherwise treat as single page.

    Args:
        html_content: Full HTML document string.

    Returns:
        List of page dicts with title and html_segment.
    """
    # Look for separator comments like <!-- PAGE: PageName -->
    sep_pattern = r"<!--\s*PAGE:\s*([^>]+)\s*-->"
    parts = re.split(sep_pattern, html_content, flags=re.IGNORECASE)

    if len(parts) <= 1:
        # No separators found: single page
        title = _extract_title(html_content) or "原型页面"
        return [{"title": title, "html_segment": html_content}]

    pages: list[dict[str, str]] = []
    # parts[0] is preamble before first separator, skip if empty
    idx = 0 if parts[0].strip() else 1
    while idx < len(parts) - 1:
        title = parts[idx].strip()
        segment = parts[idx + 1] if idx + 1 < len(parts) else ""
        pages.append({"title": title, "html_segment": segment.strip()})
        idx += 2

    return pages if pages else [{"title": "原型页面", "html_segment": html_content}]


def _extract_title(html: str) -> str | None:
    """Extract <title> from HTML."""
    import re as _re

    m = _re.search(r"<title>([^<]+)</title>", html, _re.IGNORECASE)
    return m.group(1).strip() if m else None


def build_fallback_wireframe(
    container_name: str,
    endpoints: list[dict[str, Any]],
) -> str:
    """Build a static wireframe HTML when OpenUI service is unavailable.

    Args:
        container_name: Container name for the page title.
        endpoints: Interface endpoints to display as placeholders.

    Returns:
        Static HTML string showing gray wireframe blocks.
    """
    endpoint_rows = ""
    for ep in endpoints:
        method = ep.get("method_type", "GET")
        path = ep.get("endpoint_path", "/")
        summary = ep.get("operation_summary", "")
        color = "#e9ecef"
        if method in ("POST", "PUT", "PATCH"):
            color = "#fff3cd"
        elif method == "DELETE":
            color = "#f8d7da"
        endpoint_rows += (
            f'<div style="padding:8px 12px;margin-bottom:8px;'
            f'background:{color};border:1px dashed #adb5bd;border-radius:4px;"">'
            f'<span style="font-weight:bold;color:#495057;">{method}</span> '
            f'<span style="color:#6c757d;">{path}</span>'
            f'<div style="font-size:12px;color:#868e96;margin-top:4px;">{summary}</div>'
            f"</div>"
        )

    if not endpoint_rows:
        endpoint_rows = '<div style="padding:12px;color:#868e96;">暂无接口定义</div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{container_name} - Wireframe 降级预览</title>
<style>
  body {{ margin:0; font-family:system-ui,-apple-system,sans-serif; background:#f8f9fa; }}
  .container {{ max-width:960px; margin:0 auto; padding:24px; }}
  .header {{ background:#fff; border:2px solid #dee2e6; padding:20px 24px; margin-bottom:16px; }}
  .header h1 {{ margin:0; font-size:18px; color:#212529; }}
  .block {{ background:#fff; border:2px dashed #adb5bd; padding:24px; margin-bottom:16px; min-height:120px; }}
  .block-title {{ font-size:14px; color:#868e96; margin-bottom:12px; }}
  .banner {{ background:#fff3cd; border:1px solid #ffc107; color:#856404; padding:12px 16px; margin-bottom:16px; border-radius:4px; font-size:13px; }}
</style>
</head>
<body>
<div class="container">
  <div class="banner">
    ⚠️ OpenUI 服务不可用，当前为 Wireframe 静态降级预览。请检查 Docker 状态后重试。
  </div>
  <div class="header">
    <h1>{container_name}</h1>
  </div>
  <div class="block">
    <div class="block-title">内容区占位</div>
    <div style="height:80px;background:#e9ecef;border-radius:4px;"></div>
  </div>
  <div class="block">
    <div class="block-title">接口契约概览</div>
    {endpoint_rows}
  </div>
  <div class="block">
    <div class="block-title">操作区占位</div>
    <div style="display:flex;gap:12px;">
      <div style="width:80px;height:32px;background:#e9ecef;border:1px solid #495057;border-radius:4px;"></div>
      <div style="width:80px;height:32px;background:#fff;border:1px solid #adb5bd;border-radius:4px;"></div>
    </div>
  </div>
</div>
</body>
</html>"""
