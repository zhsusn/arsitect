"""Fixtures for CLI unit tests."""

from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4.governance_fix.llm_gateway import LLMGateway
from app.services.ai_gateway import AIGateway
from app.services.git_service import GitService
from app.services.validation_service import ValidationService


class MockLLMGateway(LLMGateway):
    """Mock LLM gateway with deterministic canned responses."""

    def __init__(self, response: str = "mock llm response") -> None:
        """Initialize with a fixed response string.

        Args:
            response: Canned text returned for every generation call.
        """
        self._response = response

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        """Return the canned response."""
        return self._response

    async def generate_stream(
        self,
        prompt: str,
        on_chunk: Any,
        *,
        temperature: float = 0.2,
    ) -> str:
        """Return the canned response and optionally emit it as one chunk."""
        if on_chunk:
            result = on_chunk(self._response)
            if inspect.isawaitable(result):
                await result
        return self._response


class MockAIGateway(AIGateway):
    """Mock AI gateway with deterministic canned responses."""

    def __init__(self, response: str = "mock analysis") -> None:
        """Initialize with a fixed response string.

        Args:
            response: Canned text returned for every generation call.
        """
        super().__init__(api_key="test-key")
        self._response = response
        self.generate_non_stream = AsyncMock(return_value=response)
        self.chat = AsyncMock(return_value=f"[optimized] {response}")

    async def generate(
        self,
        prompt_name: str,
        variables: dict[str, Any],
        stream: bool = True,
    ) -> AsyncGenerator[str, None]:
        """Yield the canned response as a single chunk.

        Args:
            prompt_name: Ignored prompt name.
            variables: Ignored prompt variables.
            stream: Ignored streaming flag.

        Yields:
            Canned response chunk.
        """
        yield self._response


@pytest.fixture
def ai_gateway() -> AIGateway:
    """Return a mock AI gateway for isolated service tests."""
    return MockAIGateway(response="mock ai response")


@pytest.fixture
def bug_service(ai_gateway: AIGateway, db_session: AsyncSession):
    """Return a BugFixService wired to the mock AI gateway."""
    from app.services.bug_fix_service import BugFixService

    return BugFixService(db_session, ai_gateway=ai_gateway)


@pytest.fixture
def cli_service(db_session: AsyncSession):
    """Return a CliService bound to the test session."""
    from app.services.cli_service import CliService

    return CliService(db_session)


@pytest.fixture
def llm_gateway() -> LLMGateway:
    """Return a mock LLM gateway for isolated service tests."""
    # Return syntactically valid Python so FileBackupService.verify() passes.
    return MockLLMGateway(response='print("mock llm response")')


class MockGitService(GitService):
    """No-op git service for tests that should not touch real git state."""

    def __init__(self) -> None:
        """Initialize without a real project root."""
        super().__init__(project_root=Path.cwd())

    def is_repo(self) -> bool:
        """Always report as not a repo."""
        return False


class MockValidationService(ValidationService):
    """No-op validation service for tests."""

    def __init__(self) -> None:
        """Initialize without a real project root."""
        super().__init__(project_root=Path.cwd())

    async def validate_project(
        self,
        changed_paths: list[Any] | None = None,
    ) -> dict[str, Any]:
        """Always report success."""
        return {"ok": True, "checks": []}


@pytest.fixture
def arch_service(
    ai_gateway: AIGateway,
    llm_gateway: LLMGateway,
    db_session: AsyncSession,
):
    """Return an ArchGovernanceService wired to the mock AI/LLM gateways."""
    from app.services.arch_governance_service import ArchGovernanceService

    return ArchGovernanceService(
        db_session,
        ai_gateway=ai_gateway,
        llm_gateway=llm_gateway,
        git_service=MockGitService(),
        validation_service=MockValidationService(),
    )


@pytest.fixture
def file_backup_service(tmp_path_factory):
    """Return a FileBackupService scoped to a temporary project root."""
    from app.services.file_backup_service import FileBackupService

    root = tmp_path_factory.mktemp("project-root")
    return FileBackupService(project_root=root)
