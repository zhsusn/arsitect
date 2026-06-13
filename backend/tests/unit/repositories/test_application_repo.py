"""Tests for ApplicationRepository."""

from __future__ import annotations

import pytest

from app.infrastructure.database.repositories.application_repo import (
    ApplicationRepository,
)
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application


class TestApplicationRepository:
    """Test ApplicationRepository CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_and_get(self) -> None:
        """Can create and retrieve an application."""
        async with AsyncSessionLocal() as session:
            repo = ApplicationRepository(session)
            app = Application(
                application_id="repo-app-001",
                application_name="RepoTest",
                local_path="/tmp/repo",
            )
            created = await repo.create(app)
            assert created.application_id == "repo-app-001"

            fetched = await repo.get_by_id("repo-app-001")
            assert fetched is not None
            assert fetched.application_name == "RepoTest"

    @pytest.mark.asyncio
    async def test_list_all(self) -> None:
        """Can list applications with pagination."""
        async with AsyncSessionLocal() as session:
            repo = ApplicationRepository(session)
            for i in range(3):
                app = Application(
                    application_id=f"list-app-{i}",
                    application_name=f"ListApp{i}",
                    local_path=f"/tmp/{i}",
                )
                await repo.create(app)

            items, total = await repo.list_all(page=1, page_size=10)
            assert total >= 3
            assert len(items) >= 3

    @pytest.mark.asyncio
    async def test_update(self) -> None:
        """Can update an application."""
        import uuid

        _id = str(uuid.uuid4())
        async with AsyncSessionLocal() as session:
            repo = ApplicationRepository(session)
            app = Application(
                application_id=_id,
                application_name=f"Before-{_id[:8]}",
                local_path="/tmp/before",
            )
            await repo.create(app)

            app.application_name = f"After-{_id[:8]}"
            updated = await repo.update(app)
            assert updated.application_name == f"After-{_id[:8]}"

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        """Can delete an application."""
        async with AsyncSessionLocal() as session:
            repo = ApplicationRepository(session)
            app = Application(
                application_id="del-app-001",
                application_name="DeleteMe",
                local_path="/tmp/del",
            )
            await repo.create(app)

            result = await repo.delete("del-app-001")
            assert result is True

            fetched = await repo.get_by_id("del-app-001")
            assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self) -> None:
        """Deleting non-existent app returns False."""
        async with AsyncSessionLocal() as session:
            repo = ApplicationRepository(session)
            result = await repo.delete("no-such-id")
            assert result is False
