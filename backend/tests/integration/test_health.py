"""Integration tests for health endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app


class TestHealthEndpoint:
    """Integration tests for /api/v1/health."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Return a TestClient for the app."""
        return TestClient(app)

    def test_health_returns_200(self, client: TestClient) -> None:
        """Health endpoint returns 200 OK."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_response_schema(self, client: TestClient) -> None:
        """Health response contains required fields."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_cors_headers_present(self, client: TestClient) -> None:
        """CORS headers are present on health response."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:5173"},
        )
        assert "access-control-allow-origin" in response.headers
