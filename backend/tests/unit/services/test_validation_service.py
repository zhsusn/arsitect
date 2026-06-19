"""Tests for ValidationService."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.validation_service import ValidationService


@pytest.fixture
def validation_service(tmp_path: Path) -> ValidationService:
    """Return a ValidationService bound to a temporary directory."""
    return ValidationService(project_root=tmp_path)


async def test_validate_valid_python_file(
    validation_service: ValidationService, tmp_path: Path
) -> None:
    """TEST-1731: A valid Python file passes syntax validation."""
    target = tmp_path / "good.py"
    target.write_text("def main():\n    return 42\n", encoding="utf-8")

    result = await validation_service.validate_file(target)

    assert result["ok"] is True


async def test_validate_invalid_python_file(
    validation_service: ValidationService, tmp_path: Path
) -> None:
    """TEST-1732: An invalid Python file fails syntax validation."""
    target = tmp_path / "bad.py"
    target.write_text("def main(\n", encoding="utf-8")

    result = await validation_service.validate_file(target)

    assert result["ok"] is False
    assert "syntax error" in result["error"].lower()


async def test_validate_missing_file_returns_ok(
    validation_service: ValidationService, tmp_path: Path
) -> None:
    """TEST-1733: Validating a non-existent file returns ok."""
    target = tmp_path / "missing.py"

    result = await validation_service.validate_file(target)

    assert result["ok"] is True


async def test_validate_project_without_config_returns_ok(
    validation_service: ValidationService,
) -> None:
    """TEST-1734: A project with no build config passes validation trivially."""
    result = await validation_service.validate_project()

    assert result["ok"] is True
    assert result["checks"] == []
