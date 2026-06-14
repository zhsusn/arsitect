"""E2E test for AI CLI free-chat mode."""
from __future__ import annotations

from playwright.sync_api import Page, expect


def test_free_chat_receives_response(page: Page) -> None:
    """Free-chat mode should receive an AI response via Kimi CLI."""
    page.goto("http://127.0.0.1:5173/cli")

    textarea = page.locator('textarea[placeholder*="/"]')
    expect(textarea).to_be_visible(timeout=10000)
    expect(textarea).not_to_be_disabled()

    textarea.fill("你好")
    textarea.press("Enter")

    # User message bubble should appear.
    expect(page.locator("text=你好").first).to_be_visible(timeout=15000)

    # Wait for an AI response (anything other than the initial system messages).
    # The response may take several seconds.
    expect(page.locator("text=Arsitect").first).to_be_visible(timeout=60000)
