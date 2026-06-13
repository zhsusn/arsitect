"""Global exception hierarchy with RFC 7807 Problem Details serialization."""

from __future__ import annotations

from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application exception."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type: str = "about:blank"
    title: str = "Internal Server Error"

    def __init__(self, detail: str | None = None, instance: str | None = None) -> None:
        """Initialize with optional detail and instance URI."""
        self.detail = detail or self.title
        self.instance = instance
        super().__init__(self.detail)

    def to_problem(self) -> dict[str, Any]:
        """Serialize to RFC 7807 Problem Details."""
        problem: dict[str, Any] = {
            "type": self.error_type,
            "title": self.title,
            "status": self.status_code,
            "detail": self.detail,
        }
        if self.instance:
            problem["instance"] = self.instance
        return problem


class NotFoundError(AppError):
    """Resource not found."""

    status_code = status.HTTP_404_NOT_FOUND
    error_type = "https://api.arsitect.local/errors/not-found"
    title = "Resource Not Found"


class ConflictError(AppError):
    """Resource conflict (e.g., duplicate unique key)."""

    status_code = status.HTTP_409_CONFLICT
    error_type = "https://api.arsitect.local/errors/conflict"
    title = "Resource Conflict"


class ValidationError(AppError):
    """Request validation failed."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_type = "https://api.arsitect.local/errors/validation"
    title = "Validation Failed"


class BadRequestError(AppError):
    """Malformed request."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_type = "https://api.arsitect.local/errors/bad-request"
    title = "Bad Request"


class UnauthorizedError(AppError):
    """Authentication required."""

    status_code = status.HTTP_401_UNAUTHORIZED
    error_type = "https://api.arsitect.local/errors/unauthorized"
    title = "Unauthorized"


class ForbiddenError(AppError):
    """Permission denied."""

    status_code = status.HTTP_403_FORBIDDEN
    error_type = "https://api.arsitect.local/errors/forbidden"
    title = "Forbidden"


class ServiceUnavailableError(AppError):
    """Upstream service unavailable."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_type = "https://api.arsitect.local/errors/service-unavailable"
    title = "Service Unavailable"


def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError subclasses and return RFC 7807 Problem Details."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_problem(),
    )


def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled exceptions."""
    problem = {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "detail": str(exc) if settings.DEBUG else "An unexpected error occurred.",
    }
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=problem,
    )


# Import here to avoid circular import at module level
from app.core.config import settings  # noqa: E402
