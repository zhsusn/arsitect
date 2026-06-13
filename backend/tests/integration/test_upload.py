"""Integration tests for file upload endpoint.

NOTE: The upload endpoint is implemented in a later task (A.24).
These tests verify the endpoint contract once available.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app


class TestUploadEndpoint:
    """Integration tests for /api/v1/files/upload."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Return a TestClient for the app."""
        return TestClient(app)

    @pytest.mark.skip(reason="Upload endpoint not yet implemented (task A.24)")
    def test_upload_text_file(self, client: TestClient) -> None:
        """Upload a plain text file and receive FileUploadResult."""
        response = client.post(
            "/api/v1/files/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 201
        data = response.json()
        assert "file_id" in data
        assert data["file_name"] == "test.txt"
        assert data["mime_type"] == "text/plain"

    @pytest.mark.skip(reason="Upload endpoint not yet implemented (task A.24)")
    def test_upload_without_file_returns_422(self, client: TestClient) -> None:
        """Missing file field returns validation error."""
        response = client.post("/api/v1/files/upload")
        assert response.status_code == 422
