"""Exec stage: AI invocation layer.

Supports both the legacy HTTP invocation mode (used by early tests) and
real CLI adapters such as :class:`KimiCLIAdapter`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.services.pocketflow.cli_adapter import CLIAdapter


@dataclass
class ExecResult:
    """Result of exec stage."""

    success: bool
    output: str
    duration_ms: int
    error: str | None = None
    exit_code: int = 0
    stderr: str = ""


class ExecStage:
    """Execute AI call via CLI adapter or HTTP fallback."""

    TIMEOUT_SECONDS = 60

    def __init__(self, cli_adapter: CLIAdapter | None = None) -> None:
        """Initialize exec stage.

        Args:
            cli_adapter: Optional CLI adapter. When provided, ``execute`` will
                spawn a real subprocess via the adapter. Otherwise it falls back
                to the legacy HTTP call mode for backward compatibility.
        """
        self._cli_adapter = cli_adapter

    async def execute(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ) -> ExecResult:
        """Execute skill invocation.

        If a CLI adapter was injected, ``endpoint`` is treated as the skill path
        and ``payload`` is treated as inputs. Otherwise a legacy HTTP POST is
        sent to ``endpoint``.

        Args:
            endpoint: Skill path when using a CLI adapter, or HTTP URL otherwise.
            payload: Inputs dict when using a CLI adapter, or JSON body otherwise.

        Returns:
            ExecResult with output or error details.
        """
        if self._cli_adapter is not None:
            return await self._execute_cli(endpoint, payload)
        return await self._execute_http(endpoint, payload)

    async def _execute_cli(
        self, skill_path: str, payload: dict[str, Any]
    ) -> ExecResult:
        """Delegate to the injected CLI adapter."""
        assert self._cli_adapter is not None
        inputs = payload if isinstance(payload, dict) else {}
        result = await self._cli_adapter.execute(
            skill_path=skill_path,
            inputs={k: str(v) for k, v in inputs.items()},
            timeout=self.TIMEOUT_SECONDS,
        )
        return ExecResult(
            success=result.status == "success",
            output=result.stdout,
            duration_ms=result.duration_ms,
            error=result.stderr if result.status != "success" else None,
            exit_code=result.exit_code,
            stderr=result.stderr,
        )

    async def _execute_http(
        self, endpoint: str, payload: dict[str, Any]
    ) -> ExecResult:
        """Legacy HTTP execution mode."""
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
