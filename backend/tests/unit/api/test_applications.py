"""Tests for ApplicationRouter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app


class TestApplicationRouter:
    """Test Application CRUD endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Return a TestClient for the app."""
        return TestClient(app)

    def test_create_application(self, client: TestClient) -> None:
        """POST /api/v1/applications returns 201."""
        response = client.post(
            "/api/v1/applications",
            json={
                "application_id": "router-app-001",
                "application_name": "RouterTest",
                "local_path": ".",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["application_name"] == "RouterTest"

    def test_list_applications(self, client: TestClient) -> None:
        """GET /api/v1/applications returns paginated response."""
        response = client.get("/api/v1/applications")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "total_count" in data
        assert "page" in data

    def test_get_application(self, client: TestClient) -> None:
        """GET /api/v1/applications/{id} returns 200."""
        # Create first
        client.post(
            "/api/v1/applications",
            json={
                "application_id": "router-app-002",
                "application_name": "GetTest",
                "local_path": ".",
            },
        )
        response = client.get("/api/v1/applications/router-app-002")
        assert response.status_code == 200
        assert response.json()["application_name"] == "GetTest"

    def test_get_nonexistent(self, client: TestClient) -> None:
        """GET non-existent app returns 404."""
        response = client.get("/api/v1/applications/no-such-id")
        assert response.status_code == 404

    def test_update_application(self, client: TestClient) -> None:
        """PATCH /api/v1/applications/{id} returns 200."""
        client.post(
            "/api/v1/applications",
            json={
                "application_id": "router-app-003",
                "application_name": "Before",
                "local_path": ".",
            },
        )
        response = client.patch(
            "/api/v1/applications/router-app-003",
            json={
                "application_name": "After",
                "local_path": ".",
            },
        )
        assert response.status_code == 200
        assert response.json()["application_name"] == "After"

    def test_delete_application(self, client: TestClient) -> None:
        """DELETE /api/v1/applications/{id} returns 204."""
        client.post(
            "/api/v1/applications",
            json={
                "application_id": "router-app-004",
                "application_name": "Deletable",
                "local_path": ".",
            },
        )
        response = client.delete("/api/v1/applications/router-app-004")
        assert response.status_code == 204

    def test_delete_nonexistent(self, client: TestClient) -> None:
        """DELETE non-existent app returns 404."""
        response = client.delete("/api/v1/applications/no-such-id")
        assert response.status_code == 404

    def test_duplicate_name_conflict(self, client: TestClient) -> None:
        """Duplicate app name returns 409."""
        client.post(
            "/api/v1/applications",
            json={
                "application_id": "router-app-005",
                "application_name": "DupConflict",
                "local_path": ".",
            },
        )
        response = client.post(
            "/api/v1/applications",
            json={
                "application_id": "router-app-006",
                "application_name": "DupConflict",
                "local_path": ".",
            },
        )
        assert response.status_code == 409
