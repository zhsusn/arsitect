"""Bug fix business logic service."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.cli_session import BugFixRisk, BugRecord, BugRecordStatus
from app.schemas.cli import BugRecordCreate, ExecResult
from app.services.ai_gateway import AIGateway


class BugFixService:
    """Parses errors, finds similar bugs, analyzes root cause, and executes fixes."""

    _RISK_KEYWORDS = {
        "delete": "high",
        "drop": "high",
        "remove table": "high",
        "alter table": "medium",
        "migration": "medium",
        "refactor": "medium",
    }

    def __init__(
        self,
        session: AsyncSession,
        ai_gateway: AIGateway | None = None,
    ) -> None:
        """Initialize with an async session and optional AI gateway.

        Args:
            session: SQLAlchemy async session.
            ai_gateway: AI gateway. Defaults to a mock gateway.
        """
        self._session = session
        self._ai = ai_gateway or AIGateway()

    @staticmethod
    def parse_error(error_input: str) -> dict[str, Any]:
        """Extract error signature, type, and stack from raw input.

        Args:
            error_input: Raw error text pasted by the user.

        Returns:
            Dictionary with ``error_type``, ``error_stack``, and ``error_signature``.
        """
        error_type = "UnknownError"
        stack = ""
        lines = error_input.splitlines()

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith(("Traceback", "During")):
                continue
            match = re.search(r"([A-Z][a-zA-Z0-9_]*Error|Exception)(:\s*.*)?", stripped)
            if match:
                error_type = match.group(1)
                break

        # Simple stack extraction: lines containing "File \"".
        stack_lines = [ln for ln in lines if 'File "' in ln]
        if stack_lines:
            stack = "\n".join(stack_lines[-5:])

        signature_source = f"{error_type}:{stack_lines[-1] if stack_lines else error_input}"
        signature = hashlib.sha256(signature_source.encode()).hexdigest()[:16]

        return {
            "error_type": error_type,
            "error_stack": stack or None,
            "error_signature": signature,
        }

    async def find_similar_bugs(
        self,
        signature: str,
        threshold: float = 0.8,
        limit: int = 5,
    ) -> list[BugRecord]:
        """Find historical bugs with matching error signatures.

        Args:
            signature: Error signature to match.
            threshold: Minimum similarity ratio (MVP uses exact prefix match).
            limit: Maximum records to return.

        Returns:
            List of similar bug records.
        """
        stmt = (
            select(BugRecord)
            .where(BugRecord.error_signature == signature)
            .order_by(BugRecord.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def analyze_bug(
        self,
        error_input: str,
    ) -> dict[str, Any]:
        """Run mock AI analysis on an error.

        Args:
            error_input: Raw error text.

        Returns:
            Analysis result containing root cause and affected files.
        """
        parsed = self.parse_error(error_input)
        response = await self._ai.generate_non_stream(
            "bug_analysis", {"error_input": error_input}
        )
        root_cause = response.strip() or "Mock root cause: see analysis above."

        # Extract file paths from the stack trace.
        affected_files = re.findall(
            r'File "([^"]+)"', parsed.get("error_stack") or ""
        )
        if not affected_files:
            affected_files = ["src/main.py"]

        return {
            **parsed,
            "root_cause": root_cause,
            "affected_files": affected_files,
        }

    async def generate_fix_plan(
        self,
        bug_record_id: str,
    ) -> BugRecord:
        """Generate a fix plan for a bug record.

        Args:
            bug_record_id: Bug record ID.

        Returns:
            Updated bug record.

        Raises:
            NotFoundError: If the bug record does not exist.
        """
        bug = await self._session.get(BugRecord, bug_record_id)
        if bug is None:
            raise NotFoundError(detail=f"Bug '{bug_record_id}' not found")

        response = await self._ai.generate_non_stream(
            "fix_plan", {"root_cause": bug.root_cause or "Unknown"}
        )
        bug.fix_diff = response
        bug.fix_risk = self._assess_risk(response)
        bug.status = BugRecordStatus.PENDING
        bug.updated_at = datetime.now(UTC)
        self._session.add(bug)
        await self._session.flush()
        return bug

    async def execute_fix(
        self,
        bug_record_id: str,
        edited_diff: str | None = None,
        operator: str = "ai",
    ) -> ExecResult:
        """Simulate executing a fix plan.

        Args:
            bug_record_id: Bug record ID.
            edited_diff: Optional user-edited diff.
            operator: Execution operator.

        Returns:
            Execution result.

        Raises:
            NotFoundError: If the bug record does not exist.
            ForbiddenError: If the fix risk is high.
        """
        bug = await self._session.get(BugRecord, bug_record_id)
        if bug is None:
            raise NotFoundError(detail=f"Bug '{bug_record_id}' not found")

        if bug.status == BugRecordStatus.IGNORED:
            raise ConflictError(detail="Bug fix has been ignored")

        if bug.fix_risk == BugFixRisk.HIGH:
            raise ForbiddenError(
                detail="High risk fix should be submitted as a PR"
            )

        diff = edited_diff if edited_diff is not None else (bug.fix_diff or "")
        bug.status = BugRecordStatus.EXECUTED
        bug.executed_by = operator
        bug.updated_at = datetime.now(UTC)
        self._session.add(bug)

        # Simulate validation.
        success = len(diff) > 0 and "error" not in diff.lower()
        if success:
            bug.status = BugRecordStatus.VERIFIED
            bug.verified_result = "Mock validation passed"
        else:
            bug.status = BugRecordStatus.FAILED
            bug.verified_result = "Mock validation failed"
        bug.updated_at = datetime.now(UTC)
        self._session.add(bug)
        await self._session.flush()

        return ExecResult(
            success=success,
            output="Mock fix applied and verified." if success else "Mock fix failed.",
            error=None if success else "Validation command returned non-zero.",
            branch=f"arsitect-fix/{bug.id}",
        )

    async def ignore_fix(self, bug_record_id: str) -> BugRecord:
        """Mark a bug fix as ignored.

        Args:
            bug_record_id: Bug record ID.

        Returns:
            Updated bug record.
        """
        bug = await self._session.get(BugRecord, bug_record_id)
        if bug is None:
            raise NotFoundError(detail=f"Bug '{bug_record_id}' not found")
        bug.status = BugRecordStatus.IGNORED
        bug.updated_at = datetime.now(UTC)
        self._session.add(bug)
        await self._session.flush()
        return bug

    async def get_bug_record(self, bug_record_id: str) -> BugRecord:
        """Fetch a bug record by ID.

        Args:
            bug_record_id: Bug record ID.

        Returns:
            Bug record.

        Raises:
            NotFoundError: If the bug record does not exist.
        """
        bug = await self._session.get(BugRecord, bug_record_id)
        if bug is None:
            raise NotFoundError(detail=f"Bug '{bug_record_id}' not found")
        return bug

    async def save_bug_record(
        self,
        dto: BugRecordCreate,
        analysis: dict[str, Any] | None = None,
    ) -> BugRecord:
        """Create and persist a bug record.

        Args:
            dto: Bug record creation DTO.
            analysis: Optional precomputed analysis result.

        Returns:
            Created bug record.
        """
        if analysis is None:
            analysis = await self.analyze_bug(dto.error_input)

        similar = await self.find_similar_bugs(analysis["error_signature"], limit=1)
        similar_bug_id = similar[0].id if similar else None

        bug = BugRecord(
            project_id=dto.project_id,
            session_id=dto.session_id,
            error_signature=analysis["error_signature"],
            error_type=analysis["error_type"],
            error_input=dto.error_input,
            error_stack=analysis.get("error_stack"),
            root_cause=analysis.get("root_cause"),
            affected_files=analysis.get("affected_files"),
            fix_risk=BugFixRisk.MEDIUM,
            status=BugRecordStatus.PENDING,
            similar_bug_id=similar_bug_id,
        )
        self._session.add(bug)
        await self._session.flush()
        return bug

    def _assess_risk(self, diff: str) -> str:
        """Assess fix risk based on diff keywords.

        Args:
            diff: Generated diff.

        Returns:
            Risk level string.
        """
        lowered = diff.lower()
        for keyword, risk in self._RISK_KEYWORDS.items():
            if keyword in lowered:
                return risk
        return BugFixRisk.LOW
