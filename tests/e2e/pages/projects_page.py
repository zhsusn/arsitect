"""Project dashboard / create page object."""
from __future__ import annotations

import uuid
from pathlib import Path

import requests
from playwright.sync_api import Page, expect

from .base_page import BasePage


class ProjectsPage(BasePage):
    """Project dashboard and creation flows."""

    def create_via_api(self, api_base: str, name: str = "E2E Test Project") -> str:
        """Seed an Application + Project via API and return project id."""
        app_id = f"e2e-app-{uuid.uuid4().hex[:8]}"
        app_resp = requests.post(
            f"{api_base}/applications",
            json={
                "application_id": app_id,
                "application_name": f"{name} App",
                "local_path": str(Path(__file__).resolve().parents[3]),
                "description": "e2e",
                "workspace_id": "default",
            },
            timeout=10,
        )
        app_resp.raise_for_status()

        proj_resp = requests.post(
            f"{api_base}/applications/{app_id}/projects",
            json={
                "project_id": f"e2e-proj-{uuid.uuid4().hex[:8]}",
                "project_name": name,
                "project_description": "Created by E2E test",
                "template_level": "Standard",
            },
            timeout=10,
        )
        proj_resp.raise_for_status()
        return proj_resp.json()["project_id"]

    def open_create_modal(self) -> None:
        """Open the project create modal from the dashboard."""
        self.navigate("/projects")
        self.page.get_by_role("button", name="创建项目").first.click()
        expect(self.page.get_by_role("heading", name="创建项目")).to_be_visible()
