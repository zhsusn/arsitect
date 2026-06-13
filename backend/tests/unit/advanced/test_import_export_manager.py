"""Tests for ImportExportManager — .arsitect archive round-trip."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.advanced.import_export_manager import ImportExportManager


class TestImportExportManager:
    """ImportExportManager unit tests."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> ImportExportManager:
        """Manager using a temporary projects base directory."""
        return ImportExportManager(base_dir=str(tmp_path / "projects"))

    @pytest.fixture
    def seed_project(self, tmp_path: Path):
        """Create a sample project directory tree."""

        def _seed(project_id: str) -> Path:
            base = tmp_path / "projects" / project_id
            artifacts = base / "artifacts"
            artifacts.mkdir(parents=True, exist_ok=True)
            dsl = base / "dsl"
            dsl.mkdir(parents=True, exist_ok=True)
            config = base / "config"
            config.mkdir(parents=True, exist_ok=True)

            (artifacts / "design.md").write_text("# Design", encoding="utf-8")
            (artifacts / "diagram.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (dsl / "arsitect.aac.yml").write_text(
                "workspace:\n  model:\n    containers: []", encoding="utf-8"
            )
            (config / "project.json").write_text('{"name": "demo"}', encoding="utf-8")
            return base

        return _seed

    @pytest.mark.asyncio
    async def test_export_creates_archive(
        self,
        manager: ImportExportManager,
        seed_project,
        tmp_path: Path,
    ) -> None:
        """Export should create a .arsitect ZIP with manifest and contents."""
        seed_project("proj-exp")
        output_dir = tmp_path / "exports"

        path = await manager.export_project("proj-exp", str(output_dir))

        assert Path(path).exists()
        assert path.endswith("proj-exp.arsitect")

        import zipfile

        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            assert "manifest.json" in names
            assert any("artifacts/design.md" in n for n in names)
            assert any("dsl/arsitect.aac.yml" in n for n in names)
            assert any("config/project.json" in n for n in names)

    @pytest.mark.asyncio
    async def test_export_empty_project_still_has_manifest(
        self,
        manager: ImportExportManager,
        tmp_path: Path,
    ) -> None:
        """Exporting a project with no artifacts should still create manifest."""
        base = tmp_path / "projects" / "proj-empty"
        (base / "dsl").mkdir(parents=True)
        (base / "dsl" / "arsitect.aac.yml").write_text("workspace:", encoding="utf-8")

        path = await manager.export_project("proj-empty", str(tmp_path / "out"))

        import zipfile

        with zipfile.ZipFile(path, "r") as zf:
            assert "manifest.json" in zf.namelist()

    @pytest.mark.asyncio
    async def test_import_roundtrip(
        self,
        manager: ImportExportManager,
        seed_project,
        tmp_path: Path,
    ) -> None:
        """Import should restore project files from a .arsitect archive."""
        seed_project("proj-rt")
        export_path = await manager.export_project("proj-rt", str(tmp_path / "exports"))

        imported_id = await manager.import_project(export_path, "proj-rt-imported")
        assert imported_id == "proj-rt-imported"

        restored = tmp_path / "projects" / "proj-rt-imported"
        assert (restored / "dsl" / "arsitect.aac.yml").exists()
        assert (restored / "artifacts" / "design.md").read_text() == "# Design"
        assert (restored / "config" / "project.json").exists()

    @pytest.mark.asyncio
    async def test_import_uses_manifest_project_id(
        self,
        manager: ImportExportManager,
        seed_project,
        tmp_path: Path,
    ) -> None:
        """Import without explicit target id should use manifest project id."""
        seed_project("proj-manifest")
        export_path = await manager.export_project("proj-manifest", str(tmp_path / "exports"))

        imported_id = await manager.import_project(export_path)
        assert imported_id == "proj-manifest"

    @pytest.mark.asyncio
    async def test_import_missing_archive_raises(self, manager: ImportExportManager) -> None:
        """Importing a nonexistent archive should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await manager.import_project("/does/not/exist.arsitect")

    @pytest.mark.asyncio
    async def test_export_is_idempotent(
        self,
        manager: ImportExportManager,
        seed_project,
        tmp_path: Path,
    ) -> None:
        """Drift: repeated exports of the same project should be consistent."""
        seed_project("proj-idem")
        out = str(tmp_path / "exports")

        path_a = await manager.export_project("proj-idem", out)
        path_b = await manager.export_project("proj-idem", out)

        import zipfile

        with zipfile.ZipFile(path_a, "r") as za, zipfile.ZipFile(path_b, "r") as zb:
            assert sorted(za.namelist()) == sorted(zb.namelist())
