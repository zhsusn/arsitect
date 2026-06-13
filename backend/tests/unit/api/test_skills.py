"""Tests for SkillRegistryRouter."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from main import app


class TestSkillRegistryRouter:
    """Test skill registry endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Return a TestClient for the app."""
        return TestClient(app)

    def test_list_skills_empty(self, client: TestClient) -> None:
        """GET /skills returns empty list when no skills."""
        response = client.get("/api/v1/skills")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total_count"] == 0

    def test_scan_skills(self, client: TestClient) -> None:
        """POST /skills/import/scan scans the skills directory."""
        payload = {"directory_path": ".agents/skills"}
        response = client.post("/api/v1/skills/import/scan", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "parsed_skills" in data
        assert "conflicts" in data
        assert "errors" in data

    def test_import_confirm(self, client: TestClient) -> None:
        """POST /skills/import/confirm imports selected skills."""
        payload = {
            "skills_to_import": [
                {
                    "skill_name": f"TestSkill-{uuid.uuid4().hex[:8]}",
                    "version": "1.0.0",
                    "pattern": "generator",
                    "tags": ["test"],
                    "platforms": ["kimi"],
                    "description": "A test skill",
                    "directory_path": "/tmp/test-skill",
                    "parse_status": "PARSED",
                }
            ]
        }
        response = client.post("/api/v1/skills/import/confirm", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 1
        assert data["skipped"] == 0

    def test_get_dag(self, client: TestClient) -> None:
        """GET /skills/dag returns nodes and edges."""
        response = client.get("/api/v1/skills/dag")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

    def test_dag_changelog(self, client: TestClient) -> None:
        """GET /skills/dag/changelog returns logs."""
        response = client.get("/api/v1/skills/dag/changelog")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
