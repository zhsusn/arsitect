"""Health checker — dependency service health monitoring."""

from __future__ import annotations

import asyncio
import contextlib
import subprocess
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

import httpx


class ServiceStatus(StrEnum):
    """Health status of a dependency service."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class HealthResult:
    """Result of a single health check."""

    service: str
    status: ServiceStatus
    latency_ms: float
    message: str
    last_checked: str | None = None


CheckFn = Callable[[], Awaitable[HealthResult]]


class HealthChecker:
    """Health checker.

    Responsibilities:
    1. Register health check functions.
    2. Periodically poll registered checks.
    3. Provide status queries for fallback decisions.
    """

    def __init__(self, check_interval: float = 30.0) -> None:
        """Initialize with polling interval in seconds."""
        self.check_interval = check_interval
        self._checks: dict[str, CheckFn] = {}
        self._results: dict[str, HealthResult] = {}
        self._running = False
        self._monitor_task: asyncio.Task[None] | None = None

    def register(self, name: str, check_fn: CheckFn) -> None:
        """Register a health check function."""
        self._checks[name] = check_fn

    async def start_monitoring(self) -> None:
        """Start continuous monitoring in the background."""
        if self._running:
            return
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._monitor_task is not None:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task
            self._monitor_task = None

    async def _monitor_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            await self.check_all()
            await asyncio.sleep(self.check_interval)

    async def check_all(self) -> dict[str, HealthResult]:
        """Run all registered checks once and return results."""
        for name, check_fn in self._checks.items():
            try:
                start = datetime.now(UTC).timestamp()
                result = await asyncio.wait_for(check_fn(), timeout=5.0)
                latency = (datetime.now(UTC).timestamp() - start) * 1000
                result.latency_ms = latency
                result.last_checked = datetime.now(UTC).isoformat()
                self._results[name] = result
            except TimeoutError:
                self._results[name] = HealthResult(
                    service=name,
                    status=ServiceStatus.UNAVAILABLE,
                    latency_ms=5000.0,
                    message="Timeout",
                    last_checked=datetime.now(UTC).isoformat(),
                )
            except Exception as exc:
                self._results[name] = HealthResult(
                    service=name,
                    status=ServiceStatus.UNAVAILABLE,
                    latency_ms=0.0,
                    message=str(exc),
                    last_checked=datetime.now(UTC).isoformat(),
                )
        return dict(self._results)

    def get_status(self, service: str) -> ServiceStatus:
        """Return the current status of a service."""
        result = self._results.get(service)
        return result.status if result else ServiceStatus.UNAVAILABLE

    def is_available(self, service: str) -> bool:
        """Return True if the service is healthy."""
        return self.get_status(service) == ServiceStatus.HEALTHY

    @property
    def has_results(self) -> bool:
        """Return True if at least one health check has been executed."""
        return bool(self._results)

    async def refresh(self) -> dict[str, HealthResult]:
        """Run all registered checks once and return fresh results."""
        return await self.check_all()

    def get_all_statuses(self) -> dict[str, HealthResult]:
        """Return all current health results."""
        return dict(self._results)

    @staticmethod
    async def check_docker() -> HealthResult:
        """Check Docker daemon availability."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return HealthResult(
                    "docker",
                    ServiceStatus.HEALTHY,
                    0.0,
                    "Docker daemon running",
                )
            return HealthResult(
                "docker",
                ServiceStatus.UNAVAILABLE,
                0.0,
                result.stderr,
            )
        except Exception as exc:
            return HealthResult("docker", ServiceStatus.UNAVAILABLE, 0.0, str(exc))

    @staticmethod
    async def check_openui(base_url: str | None = None) -> HealthResult:
        """Check OpenUI service availability.

        Args:
            base_url: OpenUI service base URL. Defaults to the configured
                ``OPENUI_URL`` or ``http://localhost:3000``.
        """
        from app.core.config import settings

        url = base_url or settings.OPENUI_URL or "http://localhost:3000"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    return HealthResult(
                        "openui",
                        ServiceStatus.HEALTHY,
                        0.0,
                        "OpenUI responding",
                    )
                return HealthResult(
                    "openui",
                    ServiceStatus.UNAVAILABLE,
                    0.0,
                    f"HTTP {response.status_code}",
                )
        except Exception as exc:
            return HealthResult("openui", ServiceStatus.UNAVAILABLE, 0.0, str(exc))

    @staticmethod
    async def check_git() -> HealthResult:
        """Check Git CLI availability."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return HealthResult(
                    "git",
                    ServiceStatus.HEALTHY,
                    0.0,
                    result.stdout.strip(),
                )
            return HealthResult("git", ServiceStatus.UNAVAILABLE, 0.0, result.stderr)
        except Exception as exc:
            return HealthResult("git", ServiceStatus.UNAVAILABLE, 0.0, str(exc))

    @staticmethod
    async def check_kimi_cli() -> HealthResult:
        """Check Kimi CLI availability."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["kimi", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return HealthResult(
                    "kimi-cli",
                    ServiceStatus.HEALTHY,
                    0.0,
                    result.stdout.strip(),
                )
            return HealthResult(
                "kimi-cli",
                ServiceStatus.UNAVAILABLE,
                0.0,
                result.stderr,
            )
        except Exception as exc:
            return HealthResult("kimi-cli", ServiceStatus.UNAVAILABLE, 0.0, str(exc))


# Global singleton
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Return the global health checker singleton."""
    global _health_checker
    if _health_checker is None:
        from app.core.config import settings

        _health_checker = HealthChecker(check_interval=settings.HEALTH_CHECK_INTERVAL_SECONDS)
    return _health_checker
