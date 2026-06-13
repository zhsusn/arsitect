"""Project-level async write lock."""

from __future__ import annotations

import asyncio


class LockManager:
    """Manages per-project async write locks to prevent concurrent writes."""

    def __init__(self) -> None:
        """Initialize the lock manager."""
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, project_id: str) -> asyncio.Lock:
        """Get or create a lock for the given project."""
        if project_id not in self._locks:
            self._locks[project_id] = asyncio.Lock()
        return self._locks[project_id]

    async def acquire(self, project_id: str) -> None:
        """Acquire the lock for a project."""
        lock = self._get_lock(project_id)
        await lock.acquire()

    def release(self, project_id: str) -> None:
        """Release the lock for a project."""
        lock = self._locks.get(project_id)
        if lock is not None and lock.locked():
            lock.release()

    async def __aenter__(self) -> LockManager:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        pass
