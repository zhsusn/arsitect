"""Advanced enterprise modules for Batch-05."""

from __future__ import annotations

from app.advanced.drift_detector import DriftDetector, DriftReport
from app.advanced.history_viewer import HistoryViewer
from app.advanced.import_export_manager import ImportExportManager
from app.advanced.metrics_collector import MetricsCollector, SkillMetrics
from app.advanced.notification_manager import NotificationManager
from app.advanced.permission_manager import (
    Permission,
    PermissionManager,
    Role,
)
from app.advanced.prototype_arch_binder import (
    InterfaceGap,
    PrototypeArchBinder,
)
from app.advanced.search_engine import SearchEngine, SearchResult

__all__ = [
    "DriftDetector",
    "DriftReport",
    "HistoryViewer",
    "ImportExportManager",
    "InterfaceGap",
    "MetricsCollector",
    "NotificationManager",
    "Permission",
    "PermissionManager",
    "PrototypeArchBinder",
    "Role",
    "SearchEngine",
    "SearchResult",
    "SkillMetrics",
]
