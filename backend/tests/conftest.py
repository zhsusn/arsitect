"""Pytest fixtures and configuration."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.infrastructure.database.session as _session_mod
from app.infrastructure.database.base import Base
from app.models.application import Application  # noqa: F401
from app.models.arch_validation_session import ArchValidationSession  # noqa: F401
from app.models.artifact import ArtifactFile  # noqa: F401
from app.models.artifact_version import ArtifactVersion  # noqa: F401
from app.models.binding_rule import BindingRule  # noqa: F401
from app.models.bypass_record import BypassRecord  # noqa: F401
from app.models.canvas_state import CanvasState  # noqa: F401
from app.models.cli_session import ArchIssue, BugRecord, CliMessage, CliSession  # noqa: F401
from app.models.config_node import ConfigNode  # noqa: F401
from app.models.execution_log import ExecutionLog  # noqa: F401
from app.models.execution_plan import ExecutionPlan  # noqa: F401
from app.models.gate_decision import GateDecision  # noqa: F401
from app.models.open_ui_spec import OpenUISpec  # noqa: F401
from app.models.operation_log import OperationLog  # noqa: F401
from app.models.parallel_group import ParallelGroup  # noqa: F401
from app.models.plan_node import PlanNode  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.project_member import ProjectMember  # noqa: F401
from app.models.project_stage import ProjectStage  # noqa: F401
from app.models.rework_event import ReworkEvent  # noqa: F401
from app.models.size_estimate import SizeEstimate  # noqa: F401
from app.models.sketch import Sketch  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.skill_changelog import SkillChangeLog  # noqa: F401
from app.models.skill_dag import SkillDAGEdge, SkillDAGNode  # noqa: F401
from app.models.skill_execution import SkillExecution  # noqa: F401
from app.models.template import Template  # noqa: F401
from app.models.template_stage import TemplateStage  # noqa: F401
from app.models.wireframe import Wireframe  # noqa: F401

# Use an in-memory database with StaticPool so all connections share
# the same SQLite in-memory database.
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)


@event.listens_for(test_engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Monkeypatch module-level engine and session factory so imports work
_session_mod.engine = test_engine
_session_mod.AsyncSessionLocal = TestAsyncSessionLocal


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _init_database() -> None:
    """Create all tables once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[Any, None]:
    """Yield a fresh async session that rolls back on exit."""
    async with TestAsyncSessionLocal() as session:
        await session.begin()
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[TestClient, None]:
    """Yield a TestClient with a shared async session.

    Integration tests that span multiple HTTP requests need a single
    database session so that ``flush()`` (without ``commit()``) is
    visible across requests.
    """
    from app.infrastructure.database.session import get_db
    from main import app

    shared_session = TestAsyncSessionLocal()

    async def override_get_db():
        yield shared_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]
    await shared_session.rollback()
    await shared_session.close()
