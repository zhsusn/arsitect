"""Unit tests for BugFixService."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.cli_session import BugFixRisk, BugRecordStatus
from app.schemas.cli import BugRecordCreate
from app.services.bug_fix_service import BugFixService
from app.services.cli_service import CliService


class TestBugFixService:
    """BugFixService parsing, analysis, planning, and execution tests."""

    @pytest.fixture
    async def bug_session(self, db_session: AsyncSession) -> str:
        """Create a CLI session and return its ID for bug record fixtures."""
        cli_svc = CliService(db_session)
        session = await cli_svc.create_session("proj-1", "user-1")
        return session.id

    async def test_parse_error_with_stack(self, bug_service: BugFixService) -> None:
        """TEST-1513: parse_error extracts type, stack, and signature from traceback."""
        error_input = (
            "Traceback (most recent call last):\n"
            '  File "src/main.py", line 10, in run\n'
            "    raise ValueError('bad')\n"
            "ValueError: bad"
        )
        parsed = bug_service.parse_error(error_input)

        assert parsed["error_type"] == "ValueError"
        assert 'File "src/main.py"' in parsed["error_stack"]
        assert len(parsed["error_signature"]) == 16

    async def test_parse_error_without_stack(self, bug_service: BugFixService) -> None:
        """TEST-1514: parse_error falls back to UnknownError when no traceback is present."""
        parsed = bug_service.parse_error("Something went wrong")

        assert parsed["error_type"] == "UnknownError"
        assert parsed["error_stack"] is None
        assert len(parsed["error_signature"]) == 16

    async def test_analyze_bug(self, bug_service: BugFixService) -> None:
        """TEST-1515: analyze_bug returns root cause and affected files."""
        error_input = (
            "Traceback:\n  File \"src/app.py\", line 5, in handler\n    raise KeyError('x')\n"
        )
        result = await bug_service.analyze_bug(error_input)

        assert result["error_type"] == "KeyError"
        assert result["root_cause"] == "mock ai response"
        assert result["affected_files"] == ["src/app.py"]

    async def test_analyze_bug_default_files(self, bug_service: BugFixService) -> None:
        """TEST-1516: analyze_bug defaults affected files when the stack is empty."""
        result = await bug_service.analyze_bug("RuntimeError: fail")

        assert result["error_type"] == "RuntimeError"
        assert result["affected_files"] == ["src/main.py"]

    async def test_generate_fix_plan(
        self,
        bug_service: BugFixService,
        bug_session: str,
    ) -> None:
        """TEST-1517: generate_fix_plan populates diff and assesses risk."""
        bug = await bug_service.save_bug_record(
            BugRecordCreate(
                project_id="proj-1",
                session_id=bug_session,
                error_input="ValueError: bad",
            )
        )
        updated = await bug_service.generate_fix_plan(bug.id)

        assert updated.fix_diff == "mock ai response"
        assert updated.status == BugRecordStatus.PENDING
        assert updated.fix_risk in {BugFixRisk.LOW, BugFixRisk.MEDIUM, BugFixRisk.HIGH}

    async def test_generate_fix_plan_not_found(self, bug_service: BugFixService) -> None:
        """TEST-1518: generate_fix_plan raises NotFoundError for missing bug."""
        with pytest.raises(NotFoundError, match="Bug 'missing' not found"):
            await bug_service.generate_fix_plan("missing")

    async def test_execute_fix_success(
        self,
        bug_service: BugFixService,
        bug_session: str,
    ) -> None:
        """TEST-1519: execute_fix applies a valid diff and verifies the bug."""
        bug = await bug_service.save_bug_record(
            BugRecordCreate(
                project_id="proj-1",
                session_id=bug_session,
                error_input="ValueError: bad",
            )
        )
        bug = await bug_service.generate_fix_plan(bug.id)
        result = await bug_service.execute_fix(bug.id)

        assert result.success is True
        assert "verified" in result.output.lower()
        assert result.branch == f"arsitect-fix/{bug.id}"
        assert bug.status == BugRecordStatus.VERIFIED

    async def test_execute_fix_failure(
        self,
        bug_service: BugFixService,
        bug_session: str,
    ) -> None:
        """TEST-1520: execute_fix marks the bug failed when diff contains 'error'."""
        bug = await bug_service.save_bug_record(
            BugRecordCreate(
                project_id="proj-1",
                session_id=bug_session,
                error_input="ValueError: bad",
            )
        )
        bug.fix_diff = "error patch"
        bug.fix_risk = BugFixRisk.LOW
        await bug_service._session.flush()

        result = await bug_service.execute_fix(bug.id)

        assert result.success is False
        assert bug.status == BugRecordStatus.FAILED

    async def test_execute_fix_high_risk(
        self,
        bug_service: BugFixService,
        bug_session: str,
    ) -> None:
        """TEST-1521: High-risk fixes are rejected with ForbiddenError."""
        bug = await bug_service.save_bug_record(
            BugRecordCreate(
                project_id="proj-1",
                session_id=bug_session,
                error_input="ValueError: bad",
            )
        )
        bug.fix_risk = BugFixRisk.HIGH
        await bug_service._session.flush()

        with pytest.raises(ForbiddenError, match="High risk fix should be submitted as a PR"):
            await bug_service.execute_fix(bug.id)

    async def test_execute_fix_ignored(
        self,
        bug_service: BugFixService,
        bug_session: str,
    ) -> None:
        """TEST-1522: Executing an ignored bug raises ConflictError."""
        bug = await bug_service.save_bug_record(
            BugRecordCreate(
                project_id="proj-1",
                session_id=bug_session,
                error_input="ValueError: bad",
            )
        )
        bug.status = BugRecordStatus.IGNORED
        await bug_service._session.flush()

        with pytest.raises(ConflictError, match="Bug fix has been ignored"):
            await bug_service.execute_fix(bug.id)

    async def test_execute_fix_not_found(self, bug_service: BugFixService) -> None:
        """TEST-1523: execute_fix raises NotFoundError for missing bug."""
        with pytest.raises(NotFoundError, match="Bug 'missing' not found"):
            await bug_service.execute_fix("missing")

    async def test_save_bug_record(
        self,
        bug_service: BugFixService,
        bug_session: str,
    ) -> None:
        """TEST-1524: save_bug_record persists a parsed and analyzed bug."""
        bug = await bug_service.save_bug_record(
            BugRecordCreate(
                project_id="proj-1",
                session_id=bug_session,
                error_input="TypeError: bad type",
            )
        )

        assert bug.project_id == "proj-1"
        assert bug.session_id == bug_session
        assert bug.error_type == "TypeError"
        assert bug.status == BugRecordStatus.PENDING
        assert bug.root_cause == "mock ai response"

    async def test_save_bug_record_similar_bug(
        self,
        bug_service: BugFixService,
        bug_session: str,
    ) -> None:
        """TEST-1525: save_bug_record links a bug to a previously matching signature."""
        error_input = 'ValueError: duplicate\nTraceback:\n  File "src/a.py"\n'
        first = await bug_service.save_bug_record(
            BugRecordCreate(
                project_id="proj-1",
                session_id=bug_session,
                error_input=error_input,
            )
        )
        second = await bug_service.save_bug_record(
            BugRecordCreate(
                project_id="proj-1",
                session_id=bug_session,
                error_input=error_input,
            )
        )

        assert second.similar_bug_id == first.id
