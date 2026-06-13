"""Tests for common Pydantic schemas."""

from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.common import FileUploadResult, PageResponse, Problem


class TestProblem:
    """Test RFC 7807 Problem schema."""

    def test_serialization(self) -> None:
        """Problem serializes to expected JSON structure."""
        problem = Problem(
            type="https://api.arsitect.local/errors/not-found",
            title="Resource Not Found",
            status=404,
            detail="user 99 missing",
        )
        d = problem.model_dump()
        assert d["type"] == "https://api.arsitect.local/errors/not-found"
        assert d["title"] == "Resource Not Found"
        assert d["status"] == 404
        assert d["detail"] == "user 99 missing"
        assert d["instance"] is None

    def test_deserialization(self) -> None:
        """Problem deserializes from JSON."""
        raw = {
            "type": "about:blank",
            "title": "Bad Request",
            "status": 400,
            "detail": "Invalid input",
            "instance": "/req/42",
        }
        problem = Problem.model_validate(raw)
        assert problem.instance == "/req/42"


class TestPageResponse:
    """Test paginated response schema."""

    def test_generic_page_response(self) -> None:
        """PageResponse works with typed data."""
        resp = PageResponse[str](
            data=["a", "b", "c"],
            total_count=100,
            page=1,
            page_size=10,
            total_pages=10,
            has_next=True,
            has_previous=False,
        )
        assert resp.data == ["a", "b", "c"]
        assert resp.has_next is True


class TestFileUploadResult:
    """Test file upload result schema."""

    def test_required_fields(self) -> None:
        """Required fields must be present."""
        now = datetime.now(UTC)
        result = FileUploadResult(
            file_id="f-123",
            file_name="report.pdf",
            file_url="/files/f-123",
            mime_type="application/pdf",
            uploaded_at=now,
        )
        assert result.file_id == "f-123"
        assert result.file_size_bytes is None
        assert result.expires_at is None

    def test_optional_fields(self) -> None:
        """Optional fields can be provided."""
        now = datetime.now(UTC)
        later = datetime(2026, 12, 31, tzinfo=UTC)
        result = FileUploadResult(
            file_id="f-456",
            file_name="data.csv",
            file_url="/files/f-456",
            file_size_bytes=1024,
            mime_type="text/csv",
            uploaded_at=now,
            expires_at=later,
        )
        assert result.file_size_bytes == 1024
        assert result.expires_at == later
