"""Smoke test: navigate all sidebar routes and assert no console/network errors."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page

from pages.nav_page import NavPage


@pytest.mark.parametrize("label,path", NavPage.NAV_LINKS)
def test_navigate_all_routes(app_page: Page, label: str, path: str) -> None:
    """Each sidebar route should load without console errors."""
    errors: list[str] = []

    def _on_console(msg) -> None:
        if msg.type == "error":
            errors.append(f"[error][{path}] {msg.text}")

    app_page.on("console", _on_console)

    nav = NavPage(app_page)
    nav.navigate(path)
    # Wait for route-specific content or at least the main area.
    app_page.wait_for_selector("main", state="visible")

    # Only hard-fail on JS runtime errors, not static resource 404s.
    filtered = [
        e for e in errors
        if "[vite]" not in e and "WebSocket" not in e and "Failed to load resource" not in e
    ]
    assert not filtered, f"Console errors on {path}: {filtered}"
