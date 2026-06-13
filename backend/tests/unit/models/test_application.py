"""Tests for Application ORM model."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application


class TestApplicationModel:
    """Test Application ORM model and constraints."""

    @pytest.mark.asyncio
    async def test_create_application(self) -> None:
        """Can insert and retrieve an Application row."""
        async with AsyncSessionLocal() as session:
            app = Application(
                application_id="app-001",
                application_name="TestApp",
                local_path="/tmp/test",
                workspace_id="default",
            )
            session.add(app)
            await session.commit()

            result = await session.execute(
                select(Application).where(Application.application_id == "app-001")
            )
            fetched = result.scalar_one()
            assert fetched.application_name == "TestApp"
            assert fetched.path_accessible is True

    @pytest.mark.asyncio
    async def test_unique_constraint(self) -> None:
        """Duplicate (workspace_id, application_name) raises IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        async with AsyncSessionLocal() as session:
            app1 = Application(
                application_id="app-002",
                application_name="DupApp",
                local_path="/tmp/a",
                workspace_id="default",
            )
            session.add(app1)
            await session.commit()

            app2 = Application(
                application_id="app-003",
                application_name="DupApp",
                local_path="/tmp/b",
                workspace_id="default",
            )
            session.add(app2)
            with pytest.raises(IntegrityError):
                await session.commit()
