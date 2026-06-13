"""Tests for DriftDetector — design vs actual architecture comparison."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from app.advanced.drift_detector import DriftDetector, DriftReport
from app.c4.baseline_store import BaselineDTO


@dataclass
class FakeBaseline:
    """Fake C4 baseline for drift detector tests."""

    dsl_content: str


class FakeBaselineStore:
    """In-memory baseline store returning a preset baseline."""

    def __init__(self, baseline: FakeBaseline | None) -> None:
        self._baseline = baseline

    async def read_current(self, project_id: str) -> BaselineDTO | None:
        """Return preset baseline."""
        if self._baseline is None:
            return None
        return BaselineDTO(
            baseline_id="bl-1",
            project_id=project_id,
            version="1.0.0",
            dsl_content=self._baseline.dsl_content,
            dsl_hash="",
            level="L1-L4",
            is_current=True,
            created_at=None,
        )


class TestDriftDetector:
    """DriftDetector unit tests."""

    @pytest.fixture
    def design_dsl(self) -> str:
        """Sample DSL with ids matching code file name patterns."""
        return """
workspace:
  model:
    containers:
      - id: api_controller
        name: API Gateway
        technology: FastAPI
      - id: order_service
        name: Order Service
        technology: Python
    components:
      - id: order_handler
        name: OrderController
"""

    @pytest.mark.asyncio
    async def test_extract_design_components(self, design_dsl: str) -> None:
        """DSL parsing should extract containers and components."""
        components = DriftDetector._extract_design_components(design_dsl)
        ids = {c["id"] for c in components}
        assert ids == {"api_controller", "order_service", "order_handler"}
        assert all(c["id"] for c in components)

    @pytest.mark.asyncio
    async def test_extract_design_components_invalid_yaml(self) -> None:
        """Invalid YAML should return empty list without raising."""
        assert DriftDetector._extract_design_components("[not yaml") == []

    @pytest.mark.asyncio
    async def test_scan_code_directory(self, tmp_path: Path) -> None:
        """Code scan should discover controller/service/handler files."""
        (tmp_path / "order_controller.py").write_text("class OrderController: pass")
        (tmp_path / "order_service.py").write_text("class OrderService: pass")
        (tmp_path / "event_handler.py").write_text("class EventHandler: pass")
        (tmp_path / "README.md").write_text("# docs")

        components = DriftDetector._scan_code_directory(str(tmp_path))
        ids = {c["id"] for c in components}
        assert ids == {"order_controller", "order_service", "event_handler"}

    @pytest.mark.asyncio
    async def test_scan_missing_directory(self) -> None:
        """Scanning a nonexistent directory should return empty list."""
        assert DriftDetector._scan_code_directory("/does/not/exist") == []

    @pytest.mark.asyncio
    async def test_detect_no_drift(self, design_dsl: str, tmp_path: Path) -> None:
        """When code matches design, report should be empty."""
        (tmp_path / "api_controller.py").write_text("# api")
        (tmp_path / "order_service.py").write_text("# order")
        (tmp_path / "order_handler.py").write_text("# handler")

        store = FakeBaselineStore(FakeBaseline(design_dsl))
        detector = DriftDetector(store)
        report = await detector.detect("proj-1", str(tmp_path))

        assert isinstance(report, DriftReport)
        assert report.project_id == "proj-1"
        assert report.additions == []
        assert report.deletions == []

    @pytest.mark.asyncio
    async def test_detect_additions(self, design_dsl: str, tmp_path: Path) -> None:
        """Code files not in design should appear as additions."""
        (tmp_path / "payment_service.py").write_text("# payment")

        store = FakeBaselineStore(FakeBaseline(design_dsl))
        detector = DriftDetector(store)
        report = await detector.detect("proj-1", str(tmp_path))

        assert len(report.additions) == 1
        assert report.additions[0]["id"] == "payment_service"

    @pytest.mark.asyncio
    async def test_detect_deletions(self, design_dsl: str, tmp_path: Path) -> None:
        """Design components missing in code should appear as deletions."""
        (tmp_path / "api_controller.py").write_text("# api")

        store = FakeBaselineStore(FakeBaseline(design_dsl))
        detector = DriftDetector(store)
        report = await detector.detect("proj-1", str(tmp_path))

        deletion_ids = {c["id"] for c in report.deletions}
        assert "order_service" in deletion_ids
        assert "order_handler" in deletion_ids

    @pytest.mark.asyncio
    async def test_detect_no_baseline(self, tmp_path: Path) -> None:
        """Missing baseline should yield empty design set and report code as additions."""
        (tmp_path / "foo_controller.py").write_text("# foo")

        store = FakeBaselineStore(None)
        detector = DriftDetector(store)
        report = await detector.detect("proj-1", str(tmp_path))

        assert report.deletions == []
        assert len(report.additions) == 1
        assert report.additions[0]["id"] == "foo_controller"
