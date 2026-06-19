"""Unit tests for ArchGovernanceService fix execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.c4.governance_fix.llm_gateway import LLMGateway
from app.services.ai_gateway import AIGateway
from app.services.arch_governance_service import ArchGovernanceService
from app.services.file_backup_service import FileBackupService
from tests.unit.cli.conftest import MockGitService, MockValidationService


class SpyLLMGateway(LLMGateway):
    """Records the prompt passed to generate_stream."""

    def __init__(self, response: str = "spy response") -> None:
        self._response = response
        self.calls: list[dict[str, Any]] = []

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        return await self.generate_stream(prompt, on_chunk=None, temperature=temperature)

    async def generate_stream(
        self,
        prompt: str,
        on_chunk: Any,
        *,
        temperature: float = 0.2,
    ) -> str:
        self.calls.append({"prompt": prompt, "temperature": temperature})
        if on_chunk:
            result = on_chunk(self._response)
            if hasattr(result, "__await__"):
                await result
        return self._response


class TestArchGovernanceService:
    """Architecture governance fix plan and execution tests."""

    async def _ensure_session(self, cli_service, session_id: str, project_id: str) -> None:
        """Create a CLI session so arch_issues FK constraint is satisfied."""
        from app.models.cli_session import CliMode

        await cli_service.create_session(project_id, "user-1", CliMode.ARCH)

    async def test_optimize_change_returns_updated_change(
        self, arch_service: ArchGovernanceService
    ) -> None:
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

    async def test_apply_fix_plan_sends_progress_and_cards(
        self, arch_service: ArchGovernanceService
    ) -> None:
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

    async def test_apply_fix_plan_card_includes_change_and_strategy_prompt(
        self, arch_service: ArchGovernanceService
    ) -> None:
        """TEST-1619: decision card carries original change and strategy prompt."""
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
        plan = {
            "plans": [{"issue_ids": ["issue-1"], "changes": [change], "dry_run": True}],
            "strategy_prompt": "use modern syntax",
        }

        await arch_service.apply_fix_plan("session-1", "proj-1", plan, sender)

        cards = [m for m in sent if m.get("type") == "card"]
        assert len(cards) == 1
        card_data = cards[0]["payload"]["card"]["data"]
        assert card_data["change"] == change
        assert card_data["strategy_prompt"] == "use modern syntax"
        assert card_data["target_path"] == "backend/app/main.py"

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

    async def test_handle_change_action_fix_invokes_llm_gateway(
        self,
        ai_gateway: AIGateway,
        tmp_path: Path,
        db_session: Any,
    ) -> None:
        """TEST-1617: fix action invokes the LLM gateway with a structured prompt.

        This test verifies the architecture-governance -> Kimi CLI invocation
        link: the service assembles a prompt and delegates generation to the
        configured LLM gateway (default KimiCLIGateway in production).
        """
        spy = SpyLLMGateway(response='print("generated")')
        service = ArchGovernanceService(
            db_session,
            ai_gateway=ai_gateway,
            llm_gateway=spy,
            file_backup=FileBackupService(project_root=tmp_path),
            git_service=MockGitService(),
            validation_service=MockValidationService(),
        )
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
            "rationale": "fix missing import",
            "risk_level": "LOW",
            "auto_applicable": False,
            "requires_confirmation": True,
            "issue_id": "issue-1",
        }

        result = await service.handle_change_action(
            "session-1", "proj-1", "fix", {"change": change}, sender
        )

        assert result.success is True
        assert len(spy.calls) == 1
        prompt = spy.calls[0]["prompt"]
        assert "backend/app/main.py" in prompt
        assert "fix missing import" in prompt
        assert "资深软件架构师" in prompt
        assert target.read_text(encoding="utf-8") == 'print("generated")'

    async def test_handle_change_action_fix_falls_back_on_llm_error(
        self,
        ai_gateway: AIGateway,
        tmp_path: Path,
        db_session: Any,
    ) -> None:
        """TEST-1618: fix action falls back to the original change when LLM fails."""

        class FailingLLMGateway(LLMGateway):
            async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
                raise RuntimeError("LLM unavailable")

            async def generate_stream(
                self,
                prompt: str,
                on_chunk: Any,
                *,
                temperature: float = 0.2,
            ) -> str:
                raise RuntimeError("LLM unavailable")

        service = ArchGovernanceService(
            db_session,
            ai_gateway=ai_gateway,
            llm_gateway=FailingLLMGateway(),
            file_backup=FileBackupService(project_root=tmp_path),
            git_service=MockGitService(),
            validation_service=MockValidationService(),
        )
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
            "after": "# fallback content\n",
            "rationale": "fix",
            "risk_level": "LOW",
            "auto_applicable": False,
            "requires_confirmation": True,
            "issue_id": "issue-1",
        }

        result = await service.handle_change_action(
            "session-1", "proj-1", "fix", {"change": change}, sender
        )

        assert result.success is True
        assert target.read_text(encoding="utf-8") == "# fallback content\n"
        error_messages = [m.get("payload", {}).get("text", "") for m in sent]
        assert any("AI 调用失败" in text for text in error_messages)
