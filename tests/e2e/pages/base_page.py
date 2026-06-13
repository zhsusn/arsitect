"""Base page object with shared helpers."""
from __future__ import annotations

from playwright.sync_api import Page, expect


class BasePage:
    """Base page object."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def navigate(self, path: str) -> None:
        """Navigate to a frontend route and wait for the shell."""
        self.page.goto(f"http://localhost:5173{path}")
        expect(self.page.get_by_text("Arsitect")).to_be_visible()

    def expect_no_console_errors(self, logs: list[str]) -> None:
        """Fail if any console error was captured."""
        errors = [line for line in logs if "[error]" in line]
        assert not errors, f"Console errors detected: {errors}"
