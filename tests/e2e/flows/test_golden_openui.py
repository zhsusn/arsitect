"""Golden flow: OpenUI spec CRUD."""
from __future__ import annotations

import pytest
import requests
from playwright.sync_api import Page, expect

from pages.nav_page import NavPage
from pages.projects_page import ProjectsPage
from utils.api_mock import mock_external_services


@pytest.fixture
def seeded_project(app_page: Page, api_base: str) -> str:
    """Create an Application + Project via API for the OpenUI flow."""
    projects = ProjectsPage(app_page)
    return projects.create_via_api(api_base, name="E2E OpenUI Project")


def test_openui_spec_crud(app_page: Page, api_base: str, seeded_project: str) -> None:
    """E2E-02: OpenUI spec Create -> List -> Get -> Update -> Delete."""
    project_id = seeded_project
    mock_external_services(app_page)

    # Create
    create_resp = requests.post(
        f"{api_base}/projects/{project_id}/open-ui-specs",
        json={"spec_name": "Homepage", "status": "DRAFT"},
        timeout=10,
    )
    assert create_resp.status_code == 201, create_resp.text
    spec_id = create_resp.json()["spec_id"]

    # List
    list_resp = requests.get(f"{api_base}/projects/{project_id}/open-ui-specs", timeout=10)
    assert list_resp.status_code == 200
    assert any(s["spec_id"] == spec_id for s in list_resp.json())

    # Get
    get_resp = requests.get(f"{api_base}/open-ui-specs/{spec_id}", timeout=10)
    assert get_resp.status_code == 200
    assert get_resp.json()["spec_name"] == "Homepage"

    # Update
    update_resp = requests.patch(
        f"{api_base}/open-ui-specs/{spec_id}",
        json={"spec_name": "Dashboard", "status": "GENERATED"},
        timeout=10,
    )
    assert update_resp.status_code == 200, update_resp.text

    # Delete
    delete_resp = requests.delete(f"{api_base}/open-ui-specs/{spec_id}", timeout=10)
    assert delete_resp.status_code == 204

    # Verify page loads
    nav = NavPage(app_page)
    nav.navigate(f"/open-ui?project={project_id}")
    expect(app_page.locator("main")).to_be_visible()
