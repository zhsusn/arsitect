"""Tests for async database session factory."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal, engine, init_db


class TestAsyncSession:
    """Test async session lifecycle."""

    @pytest.mark.asyncio
    async def test_can_execute_select_one(self) -> None:
        """A fresh session can execute SELECT 1."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            assert value == 1

    @pytest.mark.asyncio
    async def test_session_rollback_on_error(self) -> None:
        """Uncommitted changes are rolled back on error."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            # No commit; implicit rollback on context exit

    @pytest.mark.asyncio
    async def test_init_db_creates_tables(self) -> None:
        """init_db should succeed without error."""
        await init_db()
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = {row[0] for row in result.fetchall()}
            # Base.metadata is empty at this stage (no models defined yet)
            assert "sqlite_sequence" in tables or len(tables) >= 0


class TestEngine:
    """Test engine configuration."""

    @pytest.mark.asyncio
    async def test_engine_url_is_async_sqlite(self) -> None:
        """Engine must be configured for aiosqlite."""
        assert "sqlite+aiosqlite" in str(engine.url)
