"""Async database engine and session factory."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.infrastructure.database.base import Base


def _is_sqlite(url: str) -> bool:
    """Return True if the database URL points to SQLite."""
    return url.startswith("sqlite")


# SQLite is file-based and handles concurrency poorly. Increase the busy-timeout
# so writers wait for readers instead of failing immediately, and keep the pool
# small to reduce lock contention.
_connect_args: dict[str, Any] = {}
_pool_kwargs: dict[str, Any] = {}
if _is_sqlite(settings.DATABASE_URL):
    # SQLite+aiosqlite supports concurrent reads under WAL, but writes are still
    # serialized. A small pool avoids the "database is locked" storm while keeping
    # enough connections for overlapping HTTP and WebSocket requests.
    _connect_args = {"timeout": 30.0}
    _pool_kwargs = {"pool_size": 5, "max_overflow": 0}


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    connect_args=_connect_args,
    **_pool_kwargs,
)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
    """Configure SQLite for better concurrency and correctness."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    if _is_sqlite(settings.DATABASE_URL):
        # WAL mode allows readers and writers to coexist without long-lived locks.
        cursor.execute("PRAGMA journal_mode=WAL")
        # busy_timeout makes writers sleep and retry instead of raising "database is locked".
        cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session for dependency injection.

    Commits the transaction when the endpoint returns successfully; rolls back
    on any unhandled exception. This ensures services that only ``flush()``
    still persist their changes across HTTP requests.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables (development only)."""
    # Ensure database directory exists for SQLite
    if settings.DATABASE_URL.startswith("sqlite"):
        url = settings.DATABASE_URL
        # Extract path after sqlite+driver:/// or sqlite:///
        db_path = url.split(":///", 1)[-1] if ":///" in url else url.split("://", 1)[-1]

        db_file = Path(db_path)
        if not db_file.is_absolute():
            db_file = Path(os.getcwd()) / db_file
        db_file.parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
