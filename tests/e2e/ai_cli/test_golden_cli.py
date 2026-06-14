"""Golden-path E2E tests for the AI CLI chat page."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from pages.cli_page import CliPage


BUG_REPORT = "TypeError: Cannot read property 'foo' of undefined at render"


def test_page_loads_and_composer_renders(cli_page: CliPage) -> None:
    """The CLI page loads and the chat composer is rendered and editable."""
    expect(cli_page.page.get_by_text("AI CLI").first).to_be_visible()
    textarea = cli_page.page.locator('textarea[placeholder*="/"]')
    expect(textarea).to_be_visible()
    expect(textarea).not_to_be_disabled()


def test_bug_report_receives_ai_analysis(cli_page: CliPage) -> None:
    """Typing a bug report produces a fix-proposal card."""
    cli_page.switch_mode("Bug 修复")
    cli_page.wait_for_message("当前模式：bug")

    cli_page.type_command(BUG_REPORT)
    cli_page.wait_for_message("收到：")
    cli_page.wait_for_message("执行修复")


def test_fix_proposal_can_be_executed(cli_page: CliPage) -> None:
    """A bug report yields a fix-proposal card that can be executed."""
    cli_page.switch_mode("Bug 修复")
    cli_page.wait_for_message("当前模式：bug")

    cli_page.type_command(BUG_REPORT)
    cli_page.wait_for_message("执行修复")

    cli_page.click_fix_button()

    cli_page.wait_for_message("Bug 修复已执行")


def test_mode_switch_between_bug_and_arch(cli_page: CliPage) -> None:
    """Slash commands switch between Bug and Arch modes."""
    cli_page.type_command("/arch")
    cli_page.wait_for_message("已切换至架构治理模式")

    cli_page.type_command("/bug")
    cli_page.wait_for_message("已切换至 Bug 修复模式")


@pytest.fixture(autouse=True)
def _fresh_session(page: Page) -> None:
    """Ensure every test begins with a clean browser context."""
    page.context.clear_cookies()
