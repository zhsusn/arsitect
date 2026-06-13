"""Artifact store with hash caching and optional Git auto-commit."""

from __future__ import annotations

import hashlib
from pathlib import Path

import aiofiles

from app.common.project_context import ProjectContext
from app.governance.artifact_version_manager import (
    ArtifactVersionManager,
    GitAdapter,
)


class ArtifactStore:
    """Unified artifact file I/O with SHA-256 caching.

    Args:
        ctx: ProjectContext for directory resolution.
        auto_git_commit: Whether to auto-commit on write.
    """

    def __init__(self, ctx: ProjectContext, auto_git_commit: bool = True) -> None:
        self.ctx = ctx
        self.auto_git_commit = auto_git_commit
        self._hash_cache: dict[str, str] = {}
        self._version_manager = ArtifactVersionManager(GitAdapter(), ctx)

        # Wire filesystem watcher for external change detection.
        from app.common.file_system_watcher import get_file_system_watcher

        get_file_system_watcher().watch_project(
            ctx.project_id, str(ctx.artifacts_dir), self
        )

    async def read(self, relative_path: str) -> str:
        """Read artifact asynchronously."""
        full_path = self.ctx.artifacts_dir / relative_path
        if not full_path.exists():
            raise FileNotFoundError(
                f"Artifact not found: {relative_path} (project={self.ctx.project_id})"
            )
        async with aiofiles.open(full_path, encoding="utf-8") as f:
            return await f.read()

    def read_sync(self, relative_path: str) -> str:
        """Read artifact synchronously."""
        full_path = self.ctx.artifacts_dir / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found: {relative_path}")
        return full_path.read_text(encoding="utf-8")

    async def write(
        self,
        relative_path: str,
        content: str,
        *,
        auto_commit: bool = True,
        commit_message: str | None = None,
    ) -> tuple[Path, str]:
        """Write artifact and return (path, sha256).

        Args:
            relative_path: Relative path within artifacts dir.
            content: File content.
            auto_commit: Whether to Git commit (overrides instance default).
            commit_message: Optional commit message.
        """
        full_path = self.ctx.artifacts_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
            await f.write(content)

        new_hash = self._compute_hash(content)
        self._hash_cache[relative_path] = new_hash

        if auto_commit and self.auto_git_commit:
            await self._version_manager.commit_artifact(
                relative_path, commit_message or f"Update {relative_path}"
            )

        return full_path, new_hash

    async def get_hash(self, relative_path: str) -> str:
        """Return SHA-256 (cached if available)."""
        if relative_path not in self._hash_cache:
            content = await self.read(relative_path)
            self._hash_cache[relative_path] = self._compute_hash(content)
        return self._hash_cache[relative_path]

    def check_external_change(self, relative_path: str) -> tuple[bool, str | None]:
        """Check if file changed externally.

        Returns:
            (changed, current_hash) — changed is True if hash differs or file missing.
        """
        full_path = self.ctx.artifacts_dir / relative_path
        if not full_path.exists():
            return True, None

        stored = self._hash_cache.get(relative_path)
        if stored is None:
            return False, None

        current = self._compute_hash(full_path.read_text(encoding="utf-8"))
        return current != stored, current

    @staticmethod
    def _compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def commit_artifact(
        self, relative_path: str, message: str | None = None
    ) -> str:
        """Explicitly commit an artifact via ArtifactVersionManager."""
        return await self._version_manager.commit_artifact(
            relative_path, message or f"Update {relative_path}"
        )

    async def get_artifact_history(
        self, relative_path: str, limit: int = 20
    ) -> list:
        """Return Git history for an artifact."""
        return await self._version_manager.get_history(relative_path, limit=limit)

    async def rollback_artifact(
        self, relative_path: str, commit_hash: str
    ) -> bool:
        """Rollback an artifact to a specific Git commit."""
        return await self._version_manager.rollback(relative_path, commit_hash)
