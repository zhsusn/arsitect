"""Tests for LogCollector."""

from __future__ import annotations

from app.services.pocketflow.log_collector import LogCollector, LogLevel


class TestLogCollector:
    """LogCollector tests."""

    def test_append_and_get(self) -> None:
        """Can append and retrieve logs."""
        lc = LogCollector()
        lc.log("prep", LogLevel.INFO, "prep started")
        lc.log("exec", LogLevel.ERROR, "exec failed")
        assert len(lc.get_logs()) == 2

    def test_filter_by_phase(self) -> None:
        """Filter logs by phase."""
        lc = LogCollector()
        lc.log("prep", LogLevel.INFO, "a")
        lc.log("exec", LogLevel.INFO, "b")
        lc.log("post", LogLevel.INFO, "c")
        exec_logs = lc.get_logs(phase="exec")
        assert len(exec_logs) == 1
        assert exec_logs[0].message == "b"

    def test_filter_by_level(self) -> None:
        """Filter logs by level."""
        lc = LogCollector()
        lc.log("prep", LogLevel.DEBUG, "d")
        lc.log("prep", LogLevel.INFO, "i")
        lc.log("prep", LogLevel.ERROR, "e")
        error_logs = lc.get_logs(level=LogLevel.ERROR)
        assert len(error_logs) == 1
        assert error_logs[0].message == "e"

    def test_min_level_filtering(self) -> None:
        """Logs below min_level are dropped."""
        lc = LogCollector(min_level=LogLevel.WARNING)
        lc.log("prep", LogLevel.DEBUG, "d")
        lc.log("prep", LogLevel.INFO, "i")
        lc.log("prep", LogLevel.WARNING, "w")
        lc.log("prep", LogLevel.ERROR, "e")
        assert len(lc.get_logs()) == 2

    def test_clear(self) -> None:
        """Clear removes all logs."""
        lc = LogCollector()
        lc.log("prep", LogLevel.INFO, "a")
        lc.clear()
        assert len(lc.get_logs()) == 0

    def test_set_min_level(self) -> None:
        """Can change min_level dynamically."""
        lc = LogCollector(min_level=LogLevel.DEBUG)
        lc.log("prep", LogLevel.DEBUG, "d")
        lc.set_min_level(LogLevel.ERROR)
        lc.log("prep", LogLevel.INFO, "i")
        assert len(lc.get_logs()) == 1
