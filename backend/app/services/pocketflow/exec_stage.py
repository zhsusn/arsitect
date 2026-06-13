"""Exec stage: AI invocation layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ExecResult:
    """Result of exec stage."""

    success: bool
    output: str
    duration_ms: int
    error: str | None = None


class ExecStage:
    """Execute AI call with HTTPX async client and 60s timeout."""

    TIMEOUT_SECONDS = 60

    async def execute(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ) -> ExecResult:
        """Execute async HTTP call.

        Args:
            endpoint: URL to call.
            payload: JSON payload.

        Returns:
            ExecResult with output or error.
        """
        import time

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                duration = int((time.time() - start) * 1000)
                return ExecResult(
                    success=True,
                    output=response.text,
                    duration_ms=duration,
                )
        except httpx.TimeoutException:
            duration = int((time.time() - start) * 1000)
            return ExecResult(
                success=False,
                output="",
                duration_ms=duration,
                error="Request timed out after 60s",
            )
        except httpx.HTTPStatusError as exc:
            duration = int((time.time() - start) * 1000)
            return ExecResult(
                success=False,
                output="",
                duration_ms=duration,
                error=f"HTTP error: {exc.response.status_code}",
            )
        except Exception as exc:  # noqa: BLE001
            duration = int((time.time() - start) * 1000)
            return ExecResult(
                success=False,
                output="",
                duration_ms=duration,
                error=str(exc),
            )
