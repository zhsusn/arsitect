"""Network interception / mock helpers for E2E tests."""
from __future__ import annotations

from playwright.sync_api import Page, Route


def mock_openui_generate(page: Page) -> None:
    """Mock OpenUI prototype generation endpoint to avoid Docker dependency."""

    def _handler(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"status":"success","html_url":"/mock/prototype.html"}',
        )

    page.route("**/api/v1/projects/*/open-ui-specs/*/generate", _handler)


def mock_external_services(page: Page) -> None:
    """Mock all slow/unstable external dependencies."""
    mock_openui_generate(page)
