"""E2E tests for the LLM Config Center Master-Detail page."""
from __future__ import annotations

import re

import pytest
import requests
from playwright.sync_api import Page, expect


LLM_CONFIG_PATH = "/settings/llm"


@pytest.fixture
def llm_page(app_page: Page, e2e_servers: dict, api_base: str) -> Page:
    """Navigate to the LLM config page with a clean default provider."""
    # Reset the default provider name in case a previous test mutated it.
    resp = requests.get(
        f"{api_base}/llm/providers",
        params={"scope": "global", "size": 1000},
        timeout=5,
    )
    resp.raise_for_status()
    default = next((n for n in resp.json()["items"] if n.get("is_default")), None)
    if default and default["name"] != "默认 Kimi CLI":
        requests.put(
            f"{api_base}/llm/providers/{default['id']}",
            json={"name": "默认 Kimi CLI"},
            timeout=5,
        )

    app_page.goto(f"{e2e_servers['frontend_url']}{LLM_CONFIG_PATH}")
    expect(app_page.get_by_text("LLM 配置中心")).to_be_visible()
    # Wait for the default provider card to render.
    expect(app_page.get_by_text("默认 Kimi CLI").first).to_be_visible(timeout=15000)
    return app_page


def test_default_provider_loaded(llm_page: Page) -> None:
    """The default Kimi CLI provider should appear in the master list."""
    expect(llm_page.get_by_text("默认 Kimi CLI").first).to_be_visible()


def test_select_provider_shows_detail(llm_page: Page) -> None:
    """Clicking a provider card should render its detail panel."""
    llm_page.get_by_text("默认 Kimi CLI").first.click()
    expect(llm_page.get_by_role("heading", name="默认 Kimi CLI")).to_be_visible()
    expect(llm_page.get_by_text("Kimi CLI").first).to_be_visible()


def test_edit_provider_opens_form(llm_page: Page) -> None:
    """Clicking edit should switch the detail panel to edit mode."""
    llm_page.get_by_text("默认 Kimi CLI").first.click()
    llm_page.get_by_role("button", name="编辑").first.click()
    expect(llm_page.get_by_role("heading", name="编辑：默认 Kimi CLI")).to_be_visible()
    expect(llm_page.get_by_role("button", name="保存")).to_be_visible()


def test_edit_provider_and_save(llm_page: Page) -> None:
    """Editing a provider name and saving should update both detail and master list."""
    llm_page.get_by_text("默认 Kimi CLI").first.click()
    llm_page.get_by_role("button", name="编辑").first.click()

    new_name = "Kimi CLI Updated"
    llm_page.get_by_test_id("provider-name-input").fill(new_name)
    llm_page.get_by_role("button", name="保存", exact=True).click()

    expect(llm_page.get_by_role("heading", name="Kimi CLI Updated")).to_be_visible()
    expect(llm_page.get_by_text(new_name).first).to_be_visible()
    # The master list card should reflect the new name as well.
    expect(llm_page.get_by_text(new_name).first).to_be_visible()


def test_cancel_resets_provider_edit(llm_page: Page) -> None:
    """Canceling an edit should revert the form and leave the original name intact."""
    llm_page.get_by_text("默认 Kimi CLI").first.click()
    llm_page.get_by_role("button", name="编辑").first.click()

    llm_page.get_by_test_id("provider-name-input").fill("Should Not Be Saved")
    llm_page.get_by_role("button", name="取消").first.click()

    expect(llm_page.get_by_role("heading", name="默认 Kimi CLI")).to_be_visible()
    expect(llm_page.get_by_text("默认 Kimi CLI").first).to_be_visible()
    expect(llm_page.get_by_text("Should Not Be Saved")).not_to_be_visible()


def test_unsaved_change_prompts_on_tab_switch(llm_page: Page) -> None:
    """A dirty provider form should show a custom unsaved-change modal before switching tabs."""
    llm_page.get_by_text("默认 Kimi CLI").first.click()
    llm_page.get_by_role("button", name="编辑").first.click()
    llm_page.get_by_test_id("provider-name-input").fill("Unsaved Change")

    llm_page.get_by_role("button", name="权限策略").click()

    modal = llm_page.get_by_role("dialog")
    expect(modal).to_be_visible()
    expect(modal).to_contain_text("未保存")
    llm_page.get_by_role("button", name="放弃并切换").click()
    expect(llm_page.get_by_text("默认 LLM 权限策略").first).to_be_visible(timeout=15000)


def test_permission_tab_renders_policy(llm_page: Page) -> None:
    """Switching to permission tab should show the default policy."""
    llm_page.get_by_role("button", name="权限策略").click()
    expect(llm_page.get_by_text("默认 LLM 权限策略").first).to_be_visible(timeout=15000)


def test_permission_edit_adds_rule(llm_page: Page) -> None:
    """Editing permission policy should allow adding a rule."""
    llm_page.get_by_role("button", name="权限策略").click()
    llm_page.get_by_text("默认 LLM 权限策略").first.click()
    llm_page.get_by_role("button", name="编辑").first.click()

    heading = llm_page.get_by_text(re.compile(r"规则列表（\d+）"))
    initial_text = heading.text_content()
    initial_count = int(re.search(r"（(\d+)）", initial_text).group(1))
    llm_page.get_by_role("button", name="+ 添加规则").first.click()
    expect(heading).to_contain_text(f"规则列表（{initial_count + 1}）")
