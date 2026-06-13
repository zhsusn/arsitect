"""Page Object Model for the AI CLI Terminal page."""
from __future__ import annotations

from playwright.sync_api import Page, expect


class CliPage:
    """Page object for /cli AI terminal interactions."""

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url
        self.page.set_default_timeout(15000)

    # ------------------------------------------------------------------
    # Navigation & presence
    # ------------------------------------------------------------------
    def navigate_to(self) -> None:
        """Open the AI CLI page and wait until the shell renders."""
        self.page.goto(f"{self.base_url}/cli")
        self.wait_for_terminal()

    def wait_for_terminal(self) -> None:
        """Wait for the xterm.js terminal to appear and the connection to open."""
        # xterm.js renders rows and a hidden textarea for input.
        expect(self.page.locator(".xterm-rows")).to_be_visible()
        expect(self.page.locator(".xterm-helper-textarea")).to_be_visible()
        # Wait for the WebSocket handshake to complete.
        expect(self.page.get_by_text("状态:")).to_be_visible()
        expect(
            self.page.get_by_text("已连接", exact=True)
        ).to_be_visible(timeout=10000)

    # ------------------------------------------------------------------
    # Terminal input
    # ------------------------------------------------------------------
    def type_command(self, command: str) -> None:
        """Focus the terminal and type a command followed by Enter."""
        # xterm.js listens to keyboard events on the terminal element. Ensure the
        # terminal canvas is focused, then type with a small delay to let xterm
        # process each keystroke.
        self.page.locator(".xterm").click()
        self.page.wait_for_timeout(100)
        self.page.keyboard.type(command, delay=20)
        self.page.keyboard.press("Enter")

    # ------------------------------------------------------------------
    # Output assertions
    # ------------------------------------------------------------------
    def wait_for_message(self, text: str, timeout: float = 15000) -> None:
        """Wait until the terminal contains the given text."""
        rows = self.page.locator(".xterm-rows")
        expect(rows).to_contain_text(text, timeout=timeout)

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
        """Click a mode tab by visible label ('Bug' or '架构')."""
        self.page.get_by_role("button", name=mode_label, exact=True).click()
