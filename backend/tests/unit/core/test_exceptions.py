"""Tests for global exception hierarchy."""

from __future__ import annotations

import pytest

from app.core.exceptions import (
    AppError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
    app_error_handler,
    generic_exception_handler,
)


class TestAppError:
    """Test base AppError behavior."""

    def test_to_problem_includes_required_fields(self) -> None:
        """RFC 7807 requires type, title, status."""
        exc = AppError(detail="something went wrong", instance="/req/123")
        problem = exc.to_problem()
        assert problem["type"] == "about:blank"
        assert problem["title"] == "Internal Server Error"
        assert problem["status"] == 500
        assert problem["detail"] == "something went wrong"
        assert problem["instance"] == "/req/123"

    def test_to_problem_omits_instance_when_none(self) -> None:
        """Instance is optional in RFC 7807."""
        exc = AppError()
        problem = exc.to_problem()
        assert "instance" not in problem


class TestConcreteExceptions:
    """Test each concrete exception subclass."""

    @pytest.mark.parametrize(
        ("cls", "expected_status", "expected_title"),
        [
            (NotFoundError, 404, "Resource Not Found"),
            (ConflictError, 409, "Resource Conflict"),
            (ValidationError, 422, "Validation Failed"),
            (BadRequestError, 400, "Bad Request"),
            (UnauthorizedError, 401, "Unauthorized"),
            (ForbiddenError, 403, "Forbidden"),
        ],
    )
    def test_status_and_title(
        self,
        cls: type[AppError],
        expected_status: int,
        expected_title: str,
    ) -> None:
        """Each exception has correct status code and title."""
        exc = cls(detail="test detail")
        problem = exc.to_problem()
        assert problem["status"] == expected_status
        assert problem["title"] == expected_title
        assert problem["detail"] == "test detail"
        assert "type" in problem


class TestHandlers:
    """Test FastAPI exception handlers."""

    @pytest.mark.asyncio
    async def test_app_error_handler_returns_json_response(self) -> None:
        """Handler must return JSONResponse with correct status."""

        exc = NotFoundError(detail="user 99 missing")
        # Minimal mock request
        response = app_error_handler(None, exc)  # type: ignore[arg-type]
        assert response.status_code == 404
        assert (
            response.body
            == b'{"type":"https://api.arsitect.local/errors/not-found","title":"Resource Not Found","status":404,"detail":"user 99 missing"}'
        )

    @pytest.mark.asyncio
    async def test_generic_handler_returns_500(self) -> None:
        """Fallback handler returns 500."""
        response = generic_exception_handler(None, RuntimeError("boom"))  # type: ignore[arg-type]
        assert response.status_code == 500
        body = response.body.decode()
        assert '"title":"Internal Server Error"' in body
        assert '"status":500' in body
