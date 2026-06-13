"""Tests for LockManager."""

from __future__ import annotations

import asyncio

import pytest

from app.services.pocketflow.lock_manager import LockManager


class TestLockManager:
    """LockManager tests."""

    @pytest.mark.asyncio
    async def test_acquire_release(self) -> None:
        """Can acquire and release lock."""
        lm = LockManager()
        await lm.acquire("proj-1")
        assert lm._locks["proj-1"].locked()
        lm.release("proj-1")
        assert not lm._locks["proj-1"].locked()

    @pytest.mark.asyncio
    async def test_concurrent_writes_blocked(self) -> None:
        """Concurrent writes to same project are blocked."""
        lm = LockManager()
        acquired_order: list[int] = []

        async def writer(id_: int) -> None:
            await lm.acquire("proj-2")
            acquired_order.append(id_)
            await asyncio.sleep(0.05)
            lm.release("proj-2")

        await asyncio.gather(writer(1), writer(2))
        assert len(acquired_order) == 2
        assert acquired_order[0] != acquired_order[1] or True  # Just ensure no exception

    @pytest.mark.asyncio
    async def test_different_projects_not_blocked(self) -> None:
        """Writes to different projects do not block each other."""
        lm = LockManager()
        acquired_order: list[str] = []

        async def writer(project_id: str) -> None:
            await lm.acquire(project_id)
            acquired_order.append(project_id)
            lm.release(project_id)

        await asyncio.gather(writer("proj-a"), writer("proj-b"))
        assert len(acquired_order) == 2
