"""Golden flow: Sketch CRUD."""
from __future__ import annotations

import pytest
import requests
from playwright.sync_api import Page, expect

from pages.nav_page import NavPage
from pages.projects_page import ProjectsPage


@pytest.fixture
def seeded_project(app_page: Page, api_base: str) -> str:
    """Create an Application + Project via API for the Sketch flow."""
    projects = ProjectsPage(app_page)
    return projects.create_via_api(api_base, name="E2E Sketch Project")


def test_sketch_crud(app_page: Page, api_base: str, seeded_project: str) -> None:
    """E2E-03: Sketch Create -> List -> Update -> Delete."""
    project_id = seeded_project

    create_resp = requests.post(
        f"{api_base}/projects/{project_id}/sketches",
        json={"name": "Landing Sketch", "status": "DRAFT"},
        timeout=10,
    )
    assert create_resp.status_code == 201, create_resp.text
    sketch_id = create_resp.json()["sketch_id"]

    list_resp = requests.get(f"{api_base}/projects/{project_id}/sketches", timeout=10)
    assert list_resp.status_code == 200
    assert any(s["sketch_id"] == sketch_id for s in list_resp.json())

    update_resp = requests.patch(
        f"{api_base}/sketches/{sketch_id}",
        json={"name": "Updated Sketch", "status": "APPROVED"},
        timeout=10,
    )
    assert update_resp.status_code == 200, update_resp.text

    delete_resp = requests.delete(f"{api_base}/sketches/{sketch_id}", timeout=10)
    assert delete_resp.status_code == 204

    nav = NavPage(app_page)
    nav.navigate(f"/sketches?project={project_id}")
    expect(app_page.locator("main")).to_be_visible()
