"""Page Object Model for the AI CLI chat page."""
from __future__ import annotations

from playwright.sync_api import Page, expect


class CliPage:
    """Page object for /cli AI chat interactions."""

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url
        self.page.set_default_timeout(15000)

    # ------------------------------------------------------------------
    # Navigation & presence
    # ------------------------------------------------------------------
    def navigate_to(self) -> None:
        """Open the AI CLI page and wait until the composer renders."""
        self.page.goto(f"{self.base_url}/cli")
        self.wait_for_composer()

    def wait_for_composer(self) -> None:
        """Wait for the chat textarea to appear and be editable."""
        textarea = self.page.locator('textarea[placeholder*="/"]')
        expect(textarea).to_be_visible()
        expect(textarea).not_to_be_disabled()

    # ------------------------------------------------------------------
    # Chat input
    # ------------------------------------------------------------------
    def type_command(self, command: str) -> None:
        """Type a command into the chat textarea and submit it.

        Escape is pressed first to dismiss any skill shortcut popup so that
        Enter submits the command rather than inserting the skill.
        """
        textarea = self.page.locator('textarea[placeholder*="/"]')
        textarea.fill(command)
        # Dismiss skill popup if it opened.
        self.page.keyboard.press("Escape")
        textarea.press("Enter")

    # ------------------------------------------------------------------
    # Output assertions
    # ------------------------------------------------------------------
    def wait_for_message(self, text: str, timeout: float = 15000) -> None:
        """Wait until the chat contains the given text."""
        expect(self.page.locator("text=" + text).first).to_be_visible(timeout=timeout)

    # ------------------------------------------------------------------
    # Card actions
    # ------------------------------------------------------------------
    def click_fix_button(self) -> None:
        """Click the primary '执行修复' button on the fix-proposal card."""
        button = self.page.get_by_role("button", name="执行修复", exact=True)
        expect(button).to_be_visible()
        button.click()

    # ------------------------------------------------------------------
    # Mode switch
    # ------------------------------------------------------------------
    def switch_mode(self, mode_label: str) -> None:
        """Click a mode tab by visible label ('Bug 修复' or '架构治理')."""
        self.page.locator("button", has_text=mode_label).first.click()
