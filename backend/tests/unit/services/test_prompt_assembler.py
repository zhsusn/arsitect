"""Tests for the PromptAssembler."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.file_backup_service import FileBackupService
from app.services.prompt_assembler import PromptAssembler


@pytest.fixture
def assembler(tmp_path: Path) -> PromptAssembler:
    """Return a PromptAssembler bound to a temporary project root."""
    return PromptAssembler(file_backup=FileBackupService(project_root=tmp_path))


def test_assemble_includes_system_role(assembler: PromptAssembler) -> None:
    """TEST-1701: The assembled prompt contains the system role."""
    change = {
        "action": "UPDATE_CODE",
        "target_path": "src/main.py",
        "before": "old",
        "after": "new",
        "rationale": "fix circular import",
        "risk_level": "MEDIUM",
    }
    prompt = assembler.assemble_arch_fix_prompt(change, "proj-1")

    assert "资深软件架构师" in prompt
    assert "修复原则" in prompt


def test_assemble_includes_issue_context(assembler: PromptAssembler) -> None:
    """TEST-1702: The prompt includes issue metadata."""
    change = {
        "action": "UPDATE_CODE",
        "target_path": "src/main.py",
        "before": "old",
        "after": "new",
        "rationale": "fix circular import",
        "risk_level": "MEDIUM",
    }
    prompt = assembler.assemble_arch_fix_prompt(change, "proj-1")

    assert "修复动作" in prompt
    assert "目标路径" in prompt
    assert "fix circular import" in prompt


def test_assemble_reads_current_code(assembler: PromptAssembler, tmp_path: Path) -> None:
    """TEST-1703: The prompt reads and embeds the current file content."""
    target = tmp_path / "src/main.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("def main():\n    pass\n", encoding="utf-8")

    change = {
        "action": "UPDATE_CODE",
        "target_path": "src/main.py",
        "before": "old",
        "after": "new",
        "rationale": "add logging",
        "risk_level": "LOW",
    }
    prompt = assembler.assemble_arch_fix_prompt(change, "proj-1")

    assert "【当前代码】" in prompt
    assert "def main():" in prompt


def test_assemble_includes_user_hint(assembler: PromptAssembler) -> None:
    """TEST-1704: A user hint is included in the prompt."""
    change = {
        "action": "UPDATE_CODE",
        "target_path": "src/main.py",
        "before": "",
        "after": "",
        "rationale": "",
        "risk_level": "LOW",
    }
    prompt = assembler.assemble_arch_fix_prompt(change, "proj-1", user_hint="不要改动接口签名")

    assert "【用户补充要求】" in prompt
    assert "不要改动接口签名" in prompt


def test_assemble_missing_file_handled_gracefully(
    assembler: PromptAssembler,
) -> None:
    """TEST-1705: Missing target files are reported gracefully."""
    change = {
        "action": "CREATE_FILE",
        "target_path": "src/new.py",
        "before": "",
        "after": "",
        "rationale": "create skeleton",
        "risk_level": "LOW",
    }
    prompt = assembler.assemble_arch_fix_prompt(change, "proj-1")

    assert "不存在" in prompt


def test_assemble_execution_instruction_format(assembler: PromptAssembler) -> None:
    """TEST-1706: The execution instruction requires the FILE block format."""
    change = {
        "action": "UPDATE_CODE",
        "target_path": "src/main.py",
        "before": "",
        "after": "",
        "rationale": "",
        "risk_level": "LOW",
    }
    prompt = assembler.assemble_arch_fix_prompt(change, "proj-1")

    assert "=== FILE:" in prompt
    assert "根因分析" in prompt
    assert "修复策略" in prompt
    assert "验证建议" in prompt
