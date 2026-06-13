"""Unit tests for ArchGovernanceService fix execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.arch_governance_service import ArchGovernanceService
from app.services.file_backup_service import FileBackupService


class TestArchGovernanceService:
    """Architecture governance fix plan and execution tests."""

    async def _ensure_session(self, cli_service, session_id: str, project_id: str) -> None:
        """Create a CLI session so arch_issues FK constraint is satisfied."""
        from app.models.cli_session import CliMode
        await cli_service.create_session(project_id, "user-1", CliMode.ARCH)

    async def test_optimize_change_returns_updated_change(self, arch_service: ArchGovernanceService) -> None:
        """TEST-1612: optimize_change calls AI gateway and returns updated change."""
        change = {
            "action": "UPDATE_CODE",
            "target_path": "backend/app/main.py",
            "before": "old",
            "after": "new",
            "rationale": "fix",
            "risk_level": "LOW",
            "auto_applicable": False,
            "requires_confirmation": True,
            "issue_id": "issue-1",
        }

        optimized = await arch_service.optimize_change("proj-1", "add logging", change)

        assert optimized["after"] == "[optimized] mock ai response"

    async def test_apply_fix_plan_sends_progress_and_cards(self, arch_service: ArchGovernanceService) -> None:
        """TEST-1613: apply_fix_plan streams progress and decision cards."""
        sent: list[dict[str, Any]] = []

        async def sender(msg: dict[str, Any]) -> None:
            sent.append(msg)

        plan = {
            "plans": [
                {
                    "issue_ids": ["issue-1"],
                    "changes": [
                        {
                            "action": "UPDATE_CODE",
                            "target_path": "backend/app/main.py",
                            "before": "old",
                            "after": "new",
                            "rationale": "fix",
                            "risk_level": "LOW",
                            "auto_applicable": False,
                            "requires_confirmation": True,
                            "issue_id": "issue-1",
                        }
                    ],
                    "dry_run": True,
                }
            ]
        }

        await arch_service.apply_fix_plan("session-1", "proj-1", plan, sender)

        types = [m.get("type") for m in sent]
        assert "progress" in types
        assert "card" in types
        assert "done" in types

    async def test_handle_change_action_skip(self, arch_service: ArchGovernanceService) -> None:
        """TEST-1614: skip action records issue as skipped."""
        sent: list[dict[str, Any]] = []

        async def sender(msg: dict[str, Any]) -> None:
            sent.append(msg)

        change = {
            "action": "UPDATE_CODE",
            "target_path": "backend/app/main.py",
            "before": "old",
            "after": "new",
            "rationale": "fix",
            "risk_level": "LOW",
            "auto_applicable": False,
            "requires_confirmation": True,
            "issue_id": "issue-1",
        }

        result = await arch_service.handle_change_action(
            "session-1", "proj-1", "skip", {"change": change}, sender
        )

        assert result.success is True
        assert result.output == "Skipped"

    async def test_handle_change_action_fix_writes_file(
        self,
        arch_service: ArchGovernanceService,
        tmp_path: Path,
    ) -> None:
        """TEST-1615: fix action writes the change to the filesystem."""
        arch_service._file_backup = FileBackupService(project_root=tmp_path)
        target = tmp_path / "backend/app/main.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("old", encoding="utf-8")

        sent: list[dict[str, Any]] = []

        async def sender(msg: dict[str, Any]) -> None:
            sent.append(msg)

        change = {
            "action": "UPDATE_CODE",
            "target_path": "backend/app/main.py",
            "before": "old",
            "after": "new",
            "rationale": "fix",
            "risk_level": "LOW",
            "auto_applicable": False,
            "requires_confirmation": True,
            "issue_id": "issue-1",
        }

        result = await arch_service.handle_change_action(
            "session-1", "proj-1", "fix", {"change": change}, sender
        )

        assert result.success is True
        # The mock LLM gateway replaces the original 'after' content.
        assert target.read_text(encoding="utf-8") == 'print("mock llm response")'

    async def test_handle_change_action_edit_uses_edited_after(
        self,
        arch_service: ArchGovernanceService,
        tmp_path: Path,
    ) -> None:
        """TEST-1616: edit action applies user-edited content."""
        arch_service._file_backup = FileBackupService(project_root=tmp_path)
        target = tmp_path / "backend/app/main.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("old", encoding="utf-8")

        sent: list[dict[str, Any]] = []

        async def sender(msg: dict[str, Any]) -> None:
            sent.append(msg)

        change = {
            "action": "UPDATE_CODE",
            "target_path": "backend/app/main.py",
            "before": "old",
            "after": "new",
            "rationale": "fix",
            "risk_level": "LOW",
            "auto_applicable": False,
            "requires_confirmation": True,
            "issue_id": "issue-1",
        }

        result = await arch_service.handle_change_action(
            "session-1", "proj-1", "edit", {"change": change, "edited_after": "edited"}, sender
        )

        assert result.success is True
        assert target.read_text(encoding="utf-8") == "edited"
