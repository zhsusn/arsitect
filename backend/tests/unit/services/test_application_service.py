"""Tests for ApplicationService."""

from __future__ import annotations

import pytest

from app.infrastructure.database.session import AsyncSessionLocal
from app.services.application_service import ApplicationService


class TestApplicationService:
    """Test ApplicationService business logic."""

    @pytest.mark.asyncio
    async def test_create_with_path_accessible(self) -> None:
        """Create app with existing path marks accessible=True."""
        async with AsyncSessionLocal() as session:
            svc = ApplicationService(session)
            app = await svc.create_application(
                application_id="svc-app-001",
                application_name="SvcTest",
                local_path=".",  # current dir exists
            )
            assert app.path_accessible is True

    @pytest.mark.asyncio
    async def test_create_with_path_inaccessible(self) -> None:
        """Create app with non-existent path marks accessible=False."""
        async with AsyncSessionLocal() as session:
            svc = ApplicationService(session)
            app = await svc.create_application(
                application_id="svc-app-002",
                application_name="Inaccessible",
                local_path="/nonexistent/path/12345",
            )
            assert app.path_accessible is False

    @pytest.mark.asyncio
    async def test_update_changes_path(self) -> None:
        """Updating path re-evaluates accessibility."""
        async with AsyncSessionLocal() as session:
            svc = ApplicationService(session)
            await svc.create_application(
                application_id="svc-app-003",
                application_name="Updatable",
                local_path="/nonexistent",
            )

            updated = await svc.update_application(
                "svc-app-003",
                local_path=".",
            )
            assert updated is not None
            assert updated.path_accessible is True

    @pytest.mark.asyncio
    async def test_check_path_accessibility(self) -> None:
        """Can re-check and update path accessibility."""
        async with AsyncSessionLocal() as session:
            svc = ApplicationService(session)
            await svc.create_application(
                application_id="svc-app-004",
                application_name="Checkable",
                local_path=".",
            )

            result = await svc.check_path_accessibility("svc-app-004")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_application(self) -> None:
        """Can delete an application."""
        async with AsyncSessionLocal() as session:
            svc = ApplicationService(session)
            await svc.create_application(
                application_id="svc-app-005",
                application_name="Deletable",
                local_path=".",
            )

            result = await svc.delete_application("svc-app-005")
            assert result is True
            assert await svc.get_application("svc-app-005") is None
