"""Golden flow: Binding rule CRUD."""
from __future__ import annotations

import pytest
import requests
from playwright.sync_api import Page, expect

from pages.nav_page import NavPage
from pages.projects_page import ProjectsPage


@pytest.fixture
def seeded_project(app_page: Page, api_base: str) -> str:
    """Create an Application + Project via API for the Binding flow."""
    projects = ProjectsPage(app_page)
    return projects.create_via_api(api_base, name="E2E Binding Project")


def test_binding_rule_crud(app_page: Page, api_base: str, seeded_project: str) -> None:
    """E2E-05: Binding rule Create -> List -> Get -> Update -> Delete."""
    project_id = seeded_project

    create_resp = requests.post(
        f"{api_base}/projects/{project_id}/binding-rules",
        json={
            "source_field": "user_id",
            "target_field": "account_id",
            "transform_type": "DIRECT",
            "status": "ACTIVE",
        },
        timeout=10,
    )
    assert create_resp.status_code == 201, create_resp.text
    binding_id = create_resp.json()["rule_id"]

    list_resp = requests.get(f"{api_base}/projects/{project_id}/binding-rules", timeout=10)
    assert list_resp.status_code == 200
    assert any(b["rule_id"] == binding_id for b in list_resp.json())

    get_resp = requests.get(f"{api_base}/binding-rules/{binding_id}", timeout=10)
    assert get_resp.status_code == 200
    assert get_resp.json()["source_field"] == "user_id"

    update_resp = requests.patch(
        f"{api_base}/binding-rules/{binding_id}",
        json={"source_field": "order_id", "status": "INACTIVE"},
        timeout=10,
    )
    assert update_resp.status_code == 200, update_resp.text

    delete_resp = requests.delete(f"{api_base}/binding-rules/{binding_id}", timeout=10)
    assert delete_resp.status_code == 204

    nav = NavPage(app_page)
    nav.navigate(f"/bindings?project={project_id}")
    expect(app_page.locator("main")).to_be_visible()
