"""Quick regression test for AI CLI chat input fix."""
from __future__ import annotations

from playwright.sync_api import Page, expect


def test_input_can_be_typed_and_sent(page: Page) -> None:
    """The AI CLI chat textarea should be editable immediately on page load."""
    page.goto("http://127.0.0.1:5173/cli")

    # Wait for the composer to render.
    textarea = page.locator('textarea[placeholder*="/"]')
    expect(textarea).to_be_visible(timeout=10000)

    # The textarea must not be disabled.
    expect(textarea).not_to_be_disabled()

    # Type something before the WebSocket necessarily connects.
    textarea.fill("hello")
    expect(textarea).to_have_value("hello")

    # Skill shortcut popup should appear after typing "/" at the start.
    textarea.fill("/bug")
    expect(page.locator("text=/bug Bug 修复")).to_be_visible()

    # Dismiss popup and send a real message.
    textarea.fill("测试输入")
    textarea.press("Enter")

    # A user message bubble should appear (added optimistically by the frontend).
    expect(page.locator("text=测试输入").first).to_be_visible(timeout=15000)
