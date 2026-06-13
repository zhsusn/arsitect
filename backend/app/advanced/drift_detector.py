"""DriftDetector — design vs actual architecture comparison."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from app.c4.baseline_store import C4BaselineStore


@dataclass
class DriftReport:
    """Drift detection report."""

    project_id: str
    checked_at: str
    additions: list[dict[str, Any]]
    deletions: list[dict[str, Any]]
    modifications: list[dict[str, Any]]


class DriftDetector:
    """Drift detector.

    Responsibilities:
    1. Extract design components from C4 DSL.
    2. Scan actual code directory for components.
    3. Generate additions/deletions/modifications report.
    """

    def __init__(self, baseline_store: C4BaselineStore) -> None:
        """Initialize with baseline store."""
        self.baseline = baseline_store

    async def detect(
        self, project_id: str, code_dir: str
    ) -> DriftReport:
        """Detect drift between design DSL and code directory."""
        baseline = await self.baseline.read_current(project_id)
        design_components = self._extract_design_components(
            baseline.dsl_content if baseline else ""
        )
        actual_components = self._scan_code_directory(code_dir)

        design_ids = {c["id"] for c in design_components}
        actual_ids = {c["id"] for c in actual_components}

        additions = [c for c in actual_components if c["id"] not in design_ids]
        deletions = [c for c in design_components if c["id"] not in actual_ids]
        modifications: list[dict[str, Any]] = []

        return DriftReport(
            project_id=project_id,
            checked_at=datetime.now(UTC).isoformat(),
            additions=additions,
            deletions=deletions,
            modifications=modifications,
        )

    @staticmethod
    def _extract_design_components(dsl_content: str) -> list[dict[str, Any]]:
        """Extract component definitions from C4 DSL."""
        try:
            data = yaml.safe_load(dsl_content) or {}
        except yaml.YAMLError:
            return []
        model = data.get("workspace", {}).get("model", {})
        components: list[dict[str, Any]] = []
        for container in model.get("containers", []):
            components.append(
                {
                    "id": container.get("id", ""),
                    "name": container.get("name", ""),
                    "type": "container",
                    "technology": container.get("technology", ""),
                }
            )
        for component in model.get("components", []):
            components.append(
                {
                    "id": component.get("id", ""),
                    "name": component.get("name", ""),
                    "type": "component",
                }
            )
        return [c for c in components if c["id"]]

    @staticmethod
    def _scan_code_directory(code_dir: str) -> list[dict[str, Any]]:
        """Scan code directory for actual components (simplified heuristic)."""
        path = Path(code_dir)
        if not path.exists():
            return []

        components: list[dict[str, Any]] = []
        seen: set[str] = set()
        for pattern in ["**/*controller*.py", "**/*service*.py", "**/*handler*.py"]:
            for file in path.rglob(pattern):
                stem = file.stem
                if stem in seen:
                    continue
                seen.add(stem)
                components.append(
                    {
                        "id": stem,
                        "name": stem,
                        "type": "code_file",
                        "path": str(file),
                    }
                )
        return components
