"""Log collector for three-phase execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class LogLevel(StrEnum):
    """Log level enum."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class LogEntry:
    """A single log entry."""

    phase: str
    level: LogLevel
    message: str
    timestamp: float = field(default_factory=lambda: __import__("time").time())


class LogCollector:
    """Collect logs from prep/exec/post phases with level filtering."""

    def __init__(self, min_level: LogLevel = LogLevel.DEBUG) -> None:
        """Initialize with a minimum log level."""
        self._logs: list[LogEntry] = []
        self._min_level = min_level
        self._level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
        }

    def log(self, phase: str, level: LogLevel, message: str) -> None:
        """Append a log entry if level >= min_level."""
        if self._level_order[level] >= self._level_order[self._min_level]:
            self._logs.append(LogEntry(phase=phase, level=level, message=message))

    def get_logs(
        self,
        phase: str | None = None,
        level: LogLevel | None = None,
    ) -> list[LogEntry]:
        """Get logs filtered by phase and/or level."""
        result = self._logs
        if phase:
            result = [log for log in result if log.phase == phase]
        if level:
            result = [log for log in result if log.level == level]
        return result

    def clear(self) -> None:
        """Clear all logs."""
        self._logs.clear()

    def set_min_level(self, level: LogLevel) -> None:
        """Update minimum log level."""
        self._min_level = level
