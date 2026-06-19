"""Tests for GitService."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.git_service import GitService


@pytest.fixture
def git_service(tmp_path: Path) -> GitService:
    """Return a GitService bound to a temporary directory."""
    return GitService(project_root=tmp_path)


def test_not_a_repo(git_service: GitService) -> None:
    """TEST-1721: A plain directory is not recognized as a git repo."""
    assert git_service.is_repo() is False
    assert git_service.current_branch() is None


def test_create_branch_fails_outside_repo(git_service: GitService) -> None:
    """TEST-1722: Branch creation fails gracefully outside a repo."""
    result = git_service.create_branch("test-branch")

    assert result["success"] is False
    assert "Not a git repository" in result["error"]


def test_commit_fails_outside_repo(git_service: GitService) -> None:
    """TEST-1723: Commit fails gracefully outside a repo."""
    result = git_service.commit("test message")

    assert result["success"] is False
    assert "Not a git repository" in result["error"]


def test_branch_name_format(git_service: GitService) -> None:
    """TEST-1724: Branch names follow the conventional format."""
    name = git_service.branch_name_for_change("issue-1")

    assert name.startswith("arsitect/arch-fix-")
    assert "issue-1" in name


def test_full_workflow_in_temporary_repo(git_service: GitService, tmp_path: Path) -> None:
    """TEST-1725: Create branch, commit and reset in a real repo."""
    import subprocess

    subprocess.run(
        ["git", "init", "--quiet"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
    )
    (tmp_path / "README.md").write_text("# hello", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "initial", "--quiet"],
        cwd=tmp_path,
        check=True,
    )

    assert git_service.is_repo() is True
    original_branch = git_service.current_branch()
    assert original_branch is not None

    branch_result = git_service.create_branch("arsitect/arch-fix-test")
    assert branch_result["success"] is True

    (tmp_path / "new.py").write_text("x = 1\n", encoding="utf-8")
    commit_result = git_service.commit("fix(arch): test commit")
    assert commit_result["success"] is True
    assert commit_result["commit"] is not None

    reset_result = git_service.reset_hard("HEAD~1")
    assert reset_result["success"] is True
    assert not (tmp_path / "new.py").exists()
