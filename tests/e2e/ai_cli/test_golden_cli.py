"""Golden-path E2E tests for the AI CLI Terminal page."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from pages.cli_page import CliPage


BUG_REPORT = "TypeError: Cannot read property 'foo' of undefined at render"


def test_page_loads_and_terminal_renders(cli_page: CliPage) -> None:
    """The CLI page loads and the xterm.js terminal is rendered."""
    expect(cli_page.page.get_by_role("heading", name="AI CLI 终端")).to_be_visible()
    expect(cli_page.page.locator(".xterm-rows")).to_be_visible()
    cli_page.wait_for_message("欢迎使用 AI CLI 终端")


def test_bug_report_receives_ai_analysis(cli_page: CliPage) -> None:
    """Typing a bug report produces an AI analysis message."""
    cli_page.type_command(BUG_REPORT)
    cli_page.wait_for_message("[AI]")


def test_fix_proposal_can_be_executed(cli_page: CliPage) -> None:
    """A bug report yields a fix-proposal card that can be executed."""
    cli_page.type_command(BUG_REPORT)
    cli_page.wait_for_message("[AI]")

    cli_page.click_fix_button()

    cli_page.wait_for_message("已执行操作：Y")


def test_mode_switch_between_bug_and_arch(cli_page: CliPage) -> None:
    """Clicking the mode tabs switches between Bug and Arch modes."""
    cli_page.switch_mode("架构")
    cli_page.wait_for_message("架构模式：")

    cli_page.switch_mode("Bug")
    cli_page.wait_for_message("Bug 模式：")


@pytest.fixture(autouse=True)
def _fresh_session(page: Page) -> None:
    """Ensure every test begins with a clean browser context."""
    page.context.clear_cookies()
