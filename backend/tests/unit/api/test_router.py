"""Tests for API v1 router registry."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app


class TestRouter:
    """Test API v1 routing."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Return a TestClient for the app."""
        return TestClient(app)

    def test_health_endpoint(self, client: TestClient) -> None:
        """GET /api/v1/health returns healthy status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_api_prefix(self, client: TestClient) -> None:
        """All v1 endpoints live under /api/v1."""
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        health_routes = [p for p in routes if "health" in p]
        assert any(p.startswith("/api/v1") for p in health_routes)

    def test_cors_preflight(self, client: TestClient) -> None:
        """CORS preflight request returns 200."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
