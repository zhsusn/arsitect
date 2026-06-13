"""Post stage: artifact collection and state update."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ArtifactReport:
    """Artifact validation report."""

    valid_count: int = 0
    invalid_count: int = 0
    missing_count: int = 0
    warnings: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PostResult:
    """Result of post stage."""

    success: bool
    artifacts: list[str]
    report: ArtifactReport
    error: str | None = None


class PostStage:
    """Validate artifacts and finalize execution."""

    MAX_SIZE_MB = 10

    async def finalize(
        self,
        expected_artifacts: list[str],
        work_dir: str,
    ) -> PostResult:
        """Finalize execution by validating artifacts.

        Args:
            expected_artifacts: List of expected artifact paths.
            work_dir: Working directory.

        Returns:
            PostResult with validation report.
        """
        artifacts: list[str] = []
        report = ArtifactReport()

        for artifact_path in expected_artifacts:
            full_path = Path(work_dir) / artifact_path
            if not full_path.exists():
                report.missing_count += 1
                report.warnings.append(
                    {
                        "artifact_path": str(artifact_path),
                        "warning_type": "MISSING_REQUIRED",
                        "message": f"Missing required artifact: {artifact_path}",
                    }
                )
                continue

            size_mb = full_path.stat().st_size / (1024 * 1024)
            if size_mb > self.MAX_SIZE_MB:
                report.warnings.append(
                    {
                        "artifact_path": str(artifact_path),
                        "warning_type": "OVERSIZED",
                        "message": f"Artifact exceeds {self.MAX_SIZE_MB}MB: {size_mb:.2f}MB",
                    }
                )

            suffix = full_path.suffix.lower()
            if suffix not in {".md", ".yaml", ".yml", ".json"}:
                report.invalid_count += 1
                report.warnings.append(
                    {
                        "artifact_path": str(artifact_path),
                        "warning_type": "FORMAT_INVALID",
                        "message": f"Unsupported format: {suffix}",
                    }
                )
            else:
                report.valid_count += 1
                artifacts.append(str(artifact_path))

        success = report.missing_count == 0
        return PostResult(
            success=success,
            artifacts=artifacts,
            report=report,
            error=None if success else f"{report.missing_count} artifacts missing",
        )
