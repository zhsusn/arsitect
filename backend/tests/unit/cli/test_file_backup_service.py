"""Unit tests for FileBackupService."""

from __future__ import annotations

import pytest

from app.services.file_backup_service import FileBackupService


class TestFileBackupService:
    """File backup, apply, verify and restore tests."""

    async def test_resolve_target_relative_path(self, file_backup_service: FileBackupService) -> None:
        """TEST-1601: Resolves a relative path inside the project root."""
        resolved = file_backup_service.resolve_target("backend/app/main.py", "proj-1")
        assert resolved == file_backup_service._project_root / "backend/app/main.py"

    async def test_resolve_target_dsl_path(self, file_backup_service: FileBackupService) -> None:
        """TEST-1602: Resolves dsl://project_id to the DSL file."""
        resolved = file_backup_service.resolve_target("dsl://proj-1", "proj-1")
        assert resolved == file_backup_service._project_root / "openspec/changes/proj-1/dsl/arsitect.aac.yml"

    async def test_resolve_target_traversal_blocked(self, file_backup_service: FileBackupService) -> None:
        """TEST-1603: Path traversal is rejected."""
        with pytest.raises(ValueError, match="Path traversal not allowed"):
            file_backup_service.resolve_target("../escape.txt", "proj-1")

    async def test_backup_existing_file(self, file_backup_service: FileBackupService) -> None:
        """TEST-1604: Backup copies an existing file."""
        target = file_backup_service._project_root / "src/foo.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("original", encoding="utf-8")

        backup = file_backup_service.backup(target, "session-1")

        assert backup.exists()
        assert backup.read_text(encoding="utf-8") == "original"

    async def test_backup_creates_marker_for_new_file(self, file_backup_service: FileBackupService) -> None:
        """TEST-1605: Backup for a non-existing file creates a create-marker."""
        target = file_backup_service._project_root / "src/new.py"
        backup = file_backup_service.backup(target, "session-1")
        assert backup.read_text(encoding="utf-8") == "__ARSITECT_BACKUP_MARKER_CREATED__"

    async def test_apply_change_writes_content(self, file_backup_service: FileBackupService) -> None:
        """TEST-1606: apply_change writes the new file content."""
        target = file_backup_service._project_root / "src/foo.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("old", encoding="utf-8")
        backup = file_backup_service.backup(target, "session-1")

        result = file_backup_service.apply_change(target, "UPDATE_CODE", "new", backup)

        assert target.read_text(encoding="utf-8") == "new"
        assert result["written"] is True

    async def test_apply_change_delete_file(self, file_backup_service: FileBackupService) -> None:
        """TEST-1607: DELETE_FILE removes the target."""
        target = file_backup_service._project_root / "src/del.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("gone", encoding="utf-8")
        backup = file_backup_service.backup(target, "session-1")

        result = file_backup_service.apply_change(target, "DELETE_FILE", None, backup)

        assert not target.exists()
        assert result["deleted"] is True

    async def test_verify_content_mismatch(self, file_backup_service: FileBackupService) -> None:
        """TEST-1608: verify reports mismatch when content differs."""
        target = file_backup_service._project_root / "src/foo.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("actual", encoding="utf-8")

        verify = file_backup_service.verify(target, "expected")

        assert verify["ok"] is False
        assert "Content mismatch" in verify["error"]

    async def test_verify_python_syntax(self, file_backup_service: FileBackupService) -> None:
        """TEST-1609: verify detects invalid Python syntax."""
        target = file_backup_service._project_root / "src/bad.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def foo(\n", encoding="utf-8")

        verify = file_backup_service.verify(target, "def foo(\n")

        assert verify["ok"] is False
        assert "syntax error" in verify["error"].lower()

    async def test_restore_from_backup(self, file_backup_service: FileBackupService) -> None:
        """TEST-1610: restore reverts a file to its backup."""
        target = file_backup_service._project_root / "src/foo.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("original", encoding="utf-8")
        backup = file_backup_service.backup(target, "session-1")
        target.write_text("changed", encoding="utf-8")

        file_backup_service.restore(backup, target)

        assert target.read_text(encoding="utf-8") == "original"

    async def test_restore_create_marker_removes_file(self, file_backup_service: FileBackupService) -> None:
        """TEST-1611: restore from create-marker removes the created file."""
        target = file_backup_service._project_root / "src/new.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        backup = file_backup_service.backup(target, "session-1")
        target.write_text("created", encoding="utf-8")

        file_backup_service.restore(backup, target)

        assert not target.exists()
