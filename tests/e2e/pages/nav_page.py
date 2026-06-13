"""Navigation sidebar page object."""
from __future__ import annotations

from playwright.sync_api import Page, expect

from .base_page import BasePage


class NavPage(BasePage):
    """Application navigation sidebar."""

    NAV_LINKS = [
        ("项目工作台", "/projects"),
        ("项目画布", "/canvas/default"),
        ("复杂度评估", "/complexity-router"),
        ("执行监控", "/executions"),
        ("监控看板", "/monitoring"),
        ("C4 架构", "/c4"),
        ("线框图", "/wireframe"),
        ("草图", "/sketches"),
        ("OpenUI", "/open-ui"),
        ("数据绑定", "/binding"),
        ("产物浏览器", "/artifacts"),
        ("架构验证", "/arch-validation"),
        ("架构治理", "/arch-governance"),
        ("历史回溯", "/history"),
        ("审批中心", "/gates"),
        ("旁路审批", "/bypass"),
        ("Application", "/applications"),
        ("Skill 治理", "/skills"),
        ("模板配置", "/template-config"),
        ("文档标准化", "/docforge"),
    ]

    def expand_group(self, group_label: str) -> None:
        """Expand a navigation group if it is collapsed."""
        button = self.page.get_by_role("button", name=group_label, exact=False)
        # Determine state via the chevron rotation by checking aria-expanded if present,
        # otherwise click to ensure expansion.
        if button.get_attribute("aria-expanded") == "false":
            button.click()

    def click_nav(self, label: str) -> None:
        """Click a navigation link by visible label."""
        self.page.get_by_role("link", name=label, exact=False).click()

    def expect_route_loaded(self, expected_path: str) -> None:
        """Assert the browser URL ends with the expected path."""
        expect(self.page).to_have_url(lambda url: url.endswith(expected_path))
