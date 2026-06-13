"""Golden flow: Bypass gate apply / list / approve."""
from __future__ import annotations

import pytest
import requests
from playwright.sync_api import Page, expect

from pages.nav_page import NavPage
from pages.projects_page import ProjectsPage


@pytest.fixture
def seeded_gate_data(app_page: Page, api_base: str) -> tuple[str, str, str, str]:
    """Create Application, Project, ExecutionPlan and pick a Stage via API."""
    projects = ProjectsPage(app_page)
    project_id = projects.create_via_api(api_base, name="E2E Bypass Project")

    plan_resp = requests.post(
        f"{api_base}/projects/{project_id}/execution-plans",
        json={"template_level": "Standard", "skill_nodes": []},
        timeout=10,
    )
    plan_resp.raise_for_status()
    plan_id = plan_resp.json()["plan_id"]

    stages_resp = requests.get(f"{api_base}/projects/{project_id}/stages", timeout=10)
    stages_resp.raise_for_status()
    stages = stages_resp.json()
    stage_id = stages[0]["stage_id"] if stages else "stage-test"

    return project_id, plan_id, stage_id, "skill-manual"


def test_bypass_apply_list_approve(
    app_page: Page, api_base: str, seeded_gate_data: tuple[str, str, str, str]
) -> None:
    """E2E-06: Apply bypass -> list -> approve."""
    project_id, plan_id, stage_id, skill_id = seeded_gate_data
    gate_id = f"gate-{project_id[-8:]}"

    apply_resp = requests.post(
        f"{api_base}/gates/{gate_id}/bypass",
        json={
            "plan_id": plan_id,
            "stage_id": stage_id,
            "skill_id": skill_id,
            "triggered_by": "e2e-tester",
            "reason": "E2E golden flow bypass",
            "authorizer_token": "token",
            "deadline_hours": 24,
        },
        timeout=10,
    )
    assert apply_resp.status_code in (200, 201), apply_resp.text
    record_id = apply_resp.json()["record_id"]

    list_resp = requests.get(f"{api_base}/projects/{project_id}/bypass-applications", timeout=10)
    assert list_resp.status_code == 200
    assert any(r["record_id"] == record_id for r in list_resp.json())

    approve_resp = requests.post(
        f"{api_base}/bypass-applications/{record_id}/approve",
        json={"approved_by": "e2e-admin"},
        timeout=10,
    )
    assert approve_resp.status_code == 200, approve_resp.text
    assert approve_resp.json()["status"] == "CLOSED"

    nav = NavPage(app_page)
    nav.navigate(f"/gate-center?project={project_id}")
    expect(app_page.locator("main")).to_be_visible()
