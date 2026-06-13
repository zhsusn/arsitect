"""File backup and safe write service for AI CLI fix execution."""

from __future__ import annotations

import difflib
import shutil
from pathlib import Path
from typing import Any

from app.core.config import settings


class FileBackupService:
    """Backup, apply, verify and restore file changes.

    All operations are constrained to the configured project root to prevent
    path traversal outside the workspace.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize with a project root.

        Args:
            project_root: Base directory for all file operations. Defaults to
                the workspace root (parent of ``backend/``).
        """
        self._project_root = (project_root or settings.project_root).resolve()
        self._backup_root = self._project_root / "data" / "backups"

    @property
    def project_root(self) -> Path:
        """Return the configured project root."""
        return self._project_root

    def resolve_target(self, target_path: str, project_id: str) -> Path:
        """Resolve a target path relative to the project root.

        Supports ``dsl://{project_id}`` as a shortcut to the assembled DSL file.

        Args:
            target_path: Relative path or ``dsl://{project_id}``.
            project_id: Project ID used to resolve DSL paths.

        Returns:
            Absolute, resolved path within the project root.

        Raises:
            ValueError: If the resolved path escapes the project root or is
                outside the allowed workspace.
        """
        if target_path.startswith("dsl://"):
            rel = Path(f"openspec/changes/{project_id}/dsl/arsitect.aac.yml")
        else:
            rel = Path(target_path)

        # Normalize and prevent traversal.
        normalized = rel.as_posix().replace("\\", "/")
        if ".." in normalized.split("/"):
            raise ValueError(f"Path traversal not allowed: {target_path}")

        absolute = (self._project_root / rel).resolve()
        # Ensure the resolved path is still inside the project root.
        try:
            absolute.relative_to(self._project_root)
        except ValueError as exc:
            raise ValueError(
                f"Target path escapes project root: {target_path}"
            ) from exc
        return absolute

    def backup(
        self,
        target_path: Path,
        session_id: str,
    ) -> Path:
        """Backup a file before modification.

        Args:
            target_path: Absolute path to the file.
            session_id: CLI session ID used to namespace backups.

        Returns:
            Path to the backup file.
        """
        backup_dir = self._backup_root / session_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            rel = target_path.relative_to(self._project_root)
        except ValueError:
            rel = target_path.name

        backup_path = backup_dir / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        if target_path.exists():
            if target_path.is_file():
                shutil.copy2(target_path, backup_path)
            else:
                # Directories are archived for DELETE_FILE support.
                archive_path = backup_path.with_suffix(".zip")
                shutil.make_archive(str(archive_path.with_suffix("")), "zip", target_path)
                backup_path = archive_path
        else:
            # Mark that the file did not exist before the change.
            backup_path.write_text("__ARSITECT_BACKUP_MARKER_CREATED__", encoding="utf-8")

        return backup_path

    def apply_change(
        self,
        target_path: Path,
        action: str,
        after: str | None,
        backup_path: Path,
    ) -> dict[str, Any]:
        """Apply a single change to the filesystem.

        Args:
            target_path: Absolute path to the target.
            action: Change action (CREATE_FILE, UPDATE_CODE, UPDATE_DOC, BOTH,
                EDIT_DSL, DELETE_FILE).
            after: New file content.
            backup_path: Path returned by ``backup``.

        Returns:
            Execution metadata.

        Raises:
            ValueError: If the action is unsupported or content is missing.
            RuntimeError: If verification fails and the file cannot be restored.
        """
        if action == "DELETE_FILE":
            if target_path.exists():
                if target_path.is_file():
                    target_path.unlink()
                else:
                    shutil.rmtree(target_path)
            return {"deleted": True, "backup": str(backup_path)}

        if after is None:
            raise ValueError(f"Missing 'after' content for action {action}")

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(after, encoding="utf-8")
        return {"written": True, "bytes": len(after.encode("utf-8"))}

    def verify(self, target_path: Path, after: str | None) -> dict[str, Any]:
        """Verify a written file.

        Args:
            target_path: Absolute path to the target.
            after: Expected content.

        Returns:
            Verification result with ``ok`` flag and optional error message.
        """
        if not target_path.exists():
            return {"ok": False, "error": "Target file does not exist after write"}

        if after is not None:
            actual = target_path.read_text(encoding="utf-8")
            if actual != after:
                diff = "\n".join(
                    difflib.unified_diff(
                        actual.splitlines(),
                        after.splitlines(),
                        lineterm="",
                        n=2,
                    )
                )
                return {"ok": False, "error": f"Content mismatch:\n{diff}"}

        # Basic syntax checks.
        suffix = target_path.suffix.lower()
        if suffix == ".py":
            import py_compile

            try:
                py_compile.compile(str(target_path), doraise=True)
            except py_compile.PyCompileError as exc:
                return {"ok": False, "error": f"Python syntax error: {exc}"}

        return {"ok": True}

    def restore(self, backup_path: Path, target_path: Path) -> None:
        """Restore a file or directory from its backup.

        Args:
            backup_path: Path returned by ``backup``.
            target_path: Absolute path to the original target.
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        marker = "__ARSITECT_BACKUP_MARKER_CREATED__"
        try:
            is_create_marker = backup_path.read_text(encoding="utf-8") == marker
        except (UnicodeDecodeError, OSError):
            is_create_marker = False

        if is_create_marker:
            # The file was created by this change; remove it.
            if target_path.exists():
                if target_path.is_file():
                    target_path.unlink()
                else:
                    shutil.rmtree(target_path)
            return

        if backup_path.suffix == ".zip":
            if target_path.exists():
                if target_path.is_file():
                    target_path.unlink()
                else:
                    shutil.rmtree(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.unpack_archive(str(backup_path), str(target_path))
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, target_path)
