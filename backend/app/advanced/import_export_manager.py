"""ImportExportManager — .arsitect project archive import/export."""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.common.project_context import ProjectContext


@dataclass
class ExportManifest:
    """Manifest inside a .arsitect archive."""

    version: str = "1.0"
    exported_at: str = ""
    project_id: str = ""
    project_name: str = ""
    includes: list[str] = field(default_factory=lambda: ["dsl", "artifacts", "config"])


class ImportExportManager:
    """Import/export manager.

    Responsibilities:
    1. Export project to .arsitect ZIP archive.
    2. Import project from .arsitect archive.
    3. Backup and restore project directories.
    """

    def __init__(self, base_dir: str = "./projects") -> None:
        """Initialize with project base directory."""
        self.base_dir = Path(base_dir)

    @staticmethod
    def _validate_project_id(project_id: str) -> None:
        """Reject project IDs that could escape the projects base directory."""
        if not project_id or ".." in project_id or "/" in project_id or "\\" in project_id:
            raise ValueError(f"Invalid project_id: {project_id}")

    async def export_project(self, project_id: str, output_path: str) -> str:
        """Export project to a .arsitect file.

        Args:
            project_id: Project identifier.
            output_path: Directory to write the archive.

        Returns:
            Path to the generated .arsitect file.
        """
        self._validate_project_id(project_id)
        with ProjectContext(project_id, base_dir=str(self.base_dir)) as ctx:
            manifest = ExportManifest(
                exported_at=datetime.now(UTC).isoformat(),
                project_id=project_id,
                project_name=project_id,
                includes=["dsl", "artifacts", "config"],
            )

            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            zip_path = output_dir / f"{project_id}.arsitect"

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(
                    "manifest.json",
                    json.dumps(
                        {
                            "version": manifest.version,
                            "exported_at": manifest.exported_at,
                            "project_id": manifest.project_id,
                            "project_name": manifest.project_name,
                            "includes": manifest.includes,
                        },
                        indent=2,
                        default=str,
                    ),
                )

                dsl_path = ctx.get_dsl_path()
                if dsl_path.exists():
                    zf.write(dsl_path, "dsl/arsitect.aac.yml")

                if ctx.artifacts_dir.exists():
                    for artifact in ctx.artifacts_dir.rglob("*"):
                        if artifact.is_file():
                            arcname = f"artifacts/{artifact.relative_to(ctx.artifacts_dir)}"
                            zf.write(artifact, arcname)

                config_path = ctx.project_dir / "config" / "project.json"
                if config_path.exists():
                    zf.write(config_path, "config/project.json")

            return str(zip_path)

    async def import_project(self, arsitect_path: str, target_project_id: str | None = None) -> str:
        """Import project from a .arsitect archive.

        Args:
            arsitect_path: Path to the .arsitect file.
            target_project_id: Optional new project ID; defaults to manifest ID.

        Returns:
            The imported project ID.
        """
        source = Path(arsitect_path)
        if not source.exists():
            raise FileNotFoundError(f"Archive not found: {arsitect_path}")

        with zipfile.ZipFile(source, "r") as zf:
            manifest_data = json.loads(zf.read("manifest.json"))
            project_id = target_project_id or manifest_data.get("project_id", "imported")
            self._validate_project_id(project_id)

            with ProjectContext(project_id, base_dir=str(self.base_dir)) as ctx:
                # Clean existing directory to avoid stale files
                if ctx.project_dir.exists():
                    shutil.rmtree(ctx.project_dir)
                ctx.project_dir.mkdir(parents=True, exist_ok=True)
                ctx.artifacts_dir.mkdir(parents=True, exist_ok=True)
                ctx.dsl_dir.mkdir(parents=True, exist_ok=True)

                # Safe extraction: reject entries that would write outside project_dir
                base = ctx.project_dir.resolve()
                for info in zf.infolist():
                    target = (base / info.filename).resolve()
                    if not os.path.commonpath([target, base]) == str(base):
                        raise ValueError(f"Unsafe archive entry: {info.filename}")
                zf.extractall(ctx.project_dir)

                # Normalize DSL location
                dsl_src = ctx.project_dir / "dsl" / "arsitect.aac.yml"
                if dsl_src.exists():
                    dsl_dst = ctx.dsl_dir / "arsitect.aac.yml"
                    dsl_dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(dsl_src), str(dsl_dst))

                return project_id
