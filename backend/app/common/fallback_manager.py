"""Fallback manager — centralized fallback decision engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.common.health_checker import HealthChecker, ServiceStatus, get_health_checker


class FallbackAction(StrEnum):
    """Possible fallback actions when a service is unavailable."""

    WIREFRAME = "wireframe"  # Degrade to wireframe UI
    SKIP = "skip"  # Skip the feature
    QUEUE = "queue"  # Queue for retry
    NOTIFY = "notify"  # Notify user only


@dataclass
class FallbackRule:
    """A fallback rule for a specific service."""

    service: str  # Service name
    action: FallbackAction  # Fallback action
    message: str  # User-facing message


class FallbackManager:
    """Fallback manager.

    Responsibilities:
    1. Define fallback strategy mappings.
    2. Trigger fallback actions based on health status.
    3. Provide user notification messages.
    """

    def __init__(self, health_checker: HealthChecker) -> None:
        """Initialize with a HealthChecker instance."""
        self.health = health_checker
        self._rules: dict[str, FallbackRule] = {}
        self._init_default_rules()

    def _init_default_rules(self) -> None:
        """Load default fallback rules."""
        self._rules = {
            "openui": FallbackRule(
                service="openui",
                action=FallbackAction.WIREFRAME,
                message="OpenUI service unavailable. Using wireframe fallback.",
            ),
            "kimi-cli": FallbackRule(
                service="kimi-cli",
                action=FallbackAction.NOTIFY,
                message="Kimi CLI unavailable. Please check your CLI installation.",
            ),
            "git": FallbackRule(
                service="git",
                action=FallbackAction.SKIP,
                message="Git unavailable. Version tracking disabled.",
            ),
        }

    def check_and_fallback(self, service: str) -> FallbackRule | None:
        """Return fallback rule if the service is unavailable."""
        status = self.health.get_status(service)
        if status != ServiceStatus.HEALTHY:
            return self._rules.get(service)
        return None

    def get_all_fallbacks(self) -> dict[str, FallbackRule]:
        """Return all rules for services that are not healthy."""
        result: dict[str, FallbackRule] = {}
        for service, rule in self._rules.items():
            if self.health.get_status(service) != ServiceStatus.HEALTHY:
                result[service] = rule
        return result

    def register_rule(self, service: str, rule: FallbackRule) -> None:
        """Register or override a fallback rule."""
        self._rules[service] = rule

    def get_rule(self, service: str) -> FallbackRule | None:
        """Return the fallback rule for a service (regardless of health)."""
        return self._rules.get(service)


# Global singleton
_fallback_manager: FallbackManager | None = None


def get_fallback_manager() -> FallbackManager:
    """Return the global fallback manager singleton."""
    global _fallback_manager
    if _fallback_manager is None:
        _fallback_manager = FallbackManager(get_health_checker())
    return _fallback_manager
