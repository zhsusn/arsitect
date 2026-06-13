"""Git helpers for architecture governance fix execution.

Creates temporary fix branches, commits applied changes and rolls back on
failure. All operations are best-effort: if the workspace is not a git repo,
the service reports the status without failing the fix.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class GitService:
    """Lightweight git wrapper for AI CLI fix workflows."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize with a project root.

        Args:
            project_root: Root directory of the git workspace. Defaults to the
                configured project root.
        """
        from app.core.config import settings

        self._project_root = (project_root or settings.project_root).resolve()

    def _run(self, args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Run a git command in the project root."""
        return subprocess.run(
            ["git", *args],
            cwd=self._project_root,
            capture_output=True,
            text=True,
            check=False,
            **kwargs,
        )

    def is_repo(self) -> bool:
        """Return True if the project root is inside a git repository."""
        result = self._run(["rev-parse", "--is-inside-work-tree"])
        return result.returncode == 0 and result.stdout.strip() == "true"

    def current_branch(self) -> str | None:
        """Return the current branch name, or None if not a repo."""
        result = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def has_changes(self) -> bool:
        """Return True if there are uncommitted changes in the workspace."""
        result = self._run(["status", "--porcelain"])
        if result.returncode != 0:
            return False
        return bool(result.stdout.strip())

    def create_branch(self, branch_name: str) -> dict[str, Any]:
        """Create and checkout a new branch from the current HEAD.

        Args:
            branch_name: Name of the branch to create.

        Returns:
            Dict with ``success``, ``branch`` and optional ``error``.
        """
        if not self.is_repo():
            return {"success": False, "error": "Not a git repository", "branch": None}

        result = self._run(["checkout", "-b", branch_name])
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Failed to create branch: {result.stderr}",
                "branch": None,
            }
        return {"success": True, "branch": branch_name, "error": None}

    def commit(self, message: str, files: list[str] | None = None) -> dict[str, Any]:
        """Stage and commit changes.

        Args:
            message: Commit message.
            files: Optional list of paths to stage. If omitted, stages all
                changes.

        Returns:
            Dict with ``success``, ``commit`` and optional ``error``.
        """
        if not self.is_repo():
            return {"success": False, "error": "Not a git repository", "commit": None}

        add_result = (
            self._run(["add", *files]) if files else self._run(["add", "-A"])
        )
        if add_result.returncode != 0:
            return {
                "success": False,
                "error": f"git add failed: {add_result.stderr}",
                "commit": None,
            }

        if not self.has_changes():
            return {"success": True, "commit": None, "error": None}

        result = self._run(["commit", "-m", message])
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"git commit failed: {result.stderr}",
                "commit": None,
            }

        commit_hash = self._run(["rev-parse", "HEAD"]).stdout.strip()
        return {"success": True, "commit": commit_hash, "error": None}

    def reset_hard(self, ref: str = "HEAD") -> dict[str, Any]:
        """Hard reset the current branch to ``ref``.

        Args:
            ref: Git ref to reset to. Defaults to HEAD.

        Returns:
            Dict with ``success`` and optional ``error``.
        """
        if not self.is_repo():
            return {"success": False, "error": "Not a git repository"}
        result = self._run(["reset", "--hard", ref])
        return {
            "success": result.returncode == 0,
            "error": result.stderr if result.returncode != 0 else None,
        }

    def checkout(self, branch: str) -> dict[str, Any]:
        """Checkout an existing branch.

        Args:
            branch: Branch name.

        Returns:
            Dict with ``success`` and optional ``error``.
        """
        if not self.is_repo():
            return {"success": False, "error": "Not a git repository"}
        result = self._run(["checkout", branch])
        return {
            "success": result.returncode == 0,
            "error": result.stderr if result.returncode != 0 else None,
        }

    def branch_name_for_change(self, issue_id: str) -> str:
        """Generate a conventional fix branch name.

        Args:
            issue_id: Issue identifier used in the branch name.

        Returns:
            Branch name like ``arsitect/arch-fix-{timestamp}-{issue_id}``.
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        suffix = issue_id or "unknown"
        return f"arsitect/arch-fix-{timestamp}-{suffix}"
