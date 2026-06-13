"""Artifact version manager — Git-based versioning, diff and rollback."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from git import Repo

from app.common.project_context import ProjectContext


@dataclass
class VersionRecord:
    """A single artifact version record."""

    commit_hash: str
    message: str
    author: str
    timestamp: datetime
    files_changed: list[str]


@dataclass
class DiffResult:
    """Diff result between two commits."""

    file_path: str
    old_content: str
    new_content: str
    added_lines: int
    removed_lines: int


class GitAdapter:
    """Git operation adapter backed by GitPython."""

    @staticmethod
    def _repo(repo_path: str) -> Repo:
        """Return a Repo instance, initializing one if necessary."""
        git_dir = Path(repo_path) / ".git"
        if git_dir.exists():
            return Repo(repo_path)
        return Repo.init(repo_path)

    @staticmethod
    def commit_file(
        repo_path: str,
        file_path: str,
        message: str,
        author: str = "system",
    ) -> str:
        """Stage and commit a single file."""
        repo = GitAdapter._repo(repo_path)
        repo.git.add(file_path)
        if repo.is_dirty() or repo.untracked_files:
            commit = repo.index.commit(message, author=author)
            return str(commit.hexsha)
        return ""

    @staticmethod
    def get_file_history(
        repo_path: str, file_path: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Return commit history for a file."""
        repo = GitAdapter._repo(repo_path)
        commits = list(repo.iter_commits(paths=file_path, max_count=limit))
        return [
            {
                "hash": c.hexsha[:8],
                "message": c.message.strip(),
                "author": str(c.author),
                "date": datetime.fromtimestamp(
                    c.committed_date, tz=UTC
                ),
                "files": list(c.stats.files.keys()),
            }
            for c in commits
        ]

    @staticmethod
    def diff_commits(
        repo_path: str,
        file_path: str,
        old_commit: str,
        new_commit: str,
    ) -> str:
        """Return textual diff for a file between two commits."""
        repo = GitAdapter._repo(repo_path)
        return repo.git.diff(f"{old_commit}..{new_commit}", "--", file_path)

    @staticmethod
    def checkout_file(
        repo_path: str, file_path: str, commit_hash: str
    ) -> bool:
        """Restore a file to a specific commit."""
        repo = GitAdapter._repo(repo_path)
        try:
            repo.git.checkout(commit_hash, "--", file_path)
            return True
        except Exception:
            return False


class ArtifactVersionManager:
    """Artifact version manager.

    Responsibilities:
    1. Auto-commit artifact changes to Git.
    2. Query version history.
    3. Diff two versions.
    4. Roll back to a specific version.
    """

    def __init__(
        self,
        git_adapter: GitAdapter,
        project_ctx: ProjectContext,
    ) -> None:
        """Initialize with a Git adapter and project context."""
        self.git = git_adapter
        self.ctx = project_ctx

    async def commit_artifact(
        self,
        relative_path: str,
        message: str,
        author: str = "system",
    ) -> str:
        """Commit an artifact change and return the commit hash."""
        full_path = self.ctx.artifacts_dir / relative_path
        # Ensure the Git repo exists.
        _repo = self.ctx.repo
        return self.git.commit_file(
            repo_path=str(self.ctx.project_dir),
            file_path=str(full_path),
            message=message,
            author=author,
        )

    async def get_history(
        self, relative_path: str, limit: int = 20
    ) -> list[VersionRecord]:
        """Return version history for an artifact."""
        full_path = self.ctx.artifacts_dir / relative_path
        commits = self.git.get_file_history(
            repo_path=str(self.ctx.project_dir),
            file_path=str(full_path),
            limit=limit,
        )
        return [
            VersionRecord(
                commit_hash=c["hash"],
                message=c["message"],
                author=c["author"],
                timestamp=c["date"],
                files_changed=c.get("files", [relative_path]),
            )
            for c in commits
        ]

    async def diff(
        self, relative_path: str, old_commit: str, new_commit: str
    ) -> DiffResult:
        """Diff an artifact between two commits."""
        diff_text = self.git.diff_commits(
            repo_path=str(self.ctx.project_dir),
            file_path=relative_path,
            old_commit=old_commit,
            new_commit=new_commit,
        )
        added = diff_text.count("\n+")
        removed = diff_text.count("\n-")
        return DiffResult(
            file_path=relative_path,
            old_content="",
            new_content="",
            added_lines=added,
            removed_lines=removed,
        )

    async def rollback(
        self, relative_path: str, commit_hash: str
    ) -> bool:
        """Rollback an artifact to a specific commit."""
        full_path = self.ctx.artifacts_dir / relative_path
        return self.git.checkout_file(
            repo_path=str(self.ctx.project_dir),
            file_path=str(full_path),
            commit_hash=commit_hash,
        )
