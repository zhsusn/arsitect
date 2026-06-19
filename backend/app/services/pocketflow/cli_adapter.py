"""CLI adapters for spawning external AI CLI tools to execute skills."""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ExecutionStatus(StrEnum):
    """Skill execution status returned by a CLI adapter."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    KILLED = "killed"


@dataclass
class CLIExecutionResult:
    """Result of a single CLI skill execution."""

    skill_id: str
    status: ExecutionStatus
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int


class CLIAdapter(ABC):
    """Abstract base class for CLI adapters that invoke skill files."""

    @abstractmethod
    async def execute(
        self,
        skill_path: str,
        inputs: dict[str, str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float = 90.0,
        kill_timeout: float = 30.0,
    ) -> CLIExecutionResult:
        """Execute a skill file and return the result.

        Args:
            skill_path: Absolute path to the skill file (e.g. SKILL.md).
            inputs: Key-value inputs passed to the skill.
            env: Additional environment variables.
            timeout: Maximum execution time in seconds.
            kill_timeout: Time to wait after SIGTERM before SIGKILL.

        Returns:
            CLIExecutionResult with stdout/stderr and exit status.
        """
        raise NotImplementedError

    def build_command(self, skill_path: str, inputs: dict[str, str] | None = None) -> list[str]:
        """Build the command line arguments for the skill invocation."""
        raise NotImplementedError


class KimiCLIAdapter(CLIAdapter):
    """Kimi CLI adapter that spawns ``kimi run <skill_file>`` subprocesses."""

    def __init__(self, kimi_cli_path: str = "kimi") -> None:
        """Initialize with the Kimi CLI executable path.

        Args:
            kimi_cli_path: Path or name of the Kimi CLI executable.
        """
        self._kimi_cli_path = kimi_cli_path

    def build_command(
        self, skill_path: str, inputs: dict[str, str] | None = None
    ) -> list[str]:
        """Build ``kimi run <skill_path> [--input key=value]...`` command."""
        cmd = [self._kimi_cli_path, "run", skill_path]
        for key, value in (inputs or {}).items():
            cmd.extend(["--input", f"{key}={value}"])
        return cmd

    async def execute(
        self,
        skill_path: str,
        inputs: dict[str, str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float = 90.0,
        kill_timeout: float = 30.0,
    ) -> CLIExecutionResult:
        """Execute the skill via Kimi CLI subprocess with timeout handling."""
        cmd = self.build_command(skill_path, inputs)
        skill_id = Path(skill_path).stem

        merged_env: dict[str, str] = {"PYTHONUNBUFFERED": "1"}
        if env:
            merged_env.update(env)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=merged_env,
        )

        start_time = time.time()
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            duration_ms = int((time.time() - start_time) * 1000)

            return CLIExecutionResult(
                skill_id=skill_id,
                status=ExecutionStatus.SUCCESS if process.returncode == 0 else ExecutionStatus.ERROR,
                exit_code=process.returncode or 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                duration_ms=duration_ms,
            )

        except TimeoutError:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=kill_timeout)
            except TimeoutError:
                process.kill()
                await process.wait()

            return CLIExecutionResult(
                skill_id=skill_id,
                status=ExecutionStatus.KILLED,
                exit_code=-1,
                stdout="",
                stderr=f"Execution timed out after {timeout}s (SIGKILL)",
                duration_ms=int(timeout * 1000),
            )


class MockCLIAdapter(CLIAdapter):
    """In-memory CLI adapter for testing and offline environments.

    Returns a preset result based on the skill path.
    """

    def __init__(
        self,
        result: CLIExecutionResult | None = None,
        results: dict[str, CLIExecutionResult] | None = None,
    ) -> None:
        """Initialize with a default result or per-skill results.

        Args:
            result: Default result for any skill path.
            results: Mapping from skill path to result.
        """
        self._default = result
        self._results = results or {}

    def build_command(self, skill_path: str, inputs: dict[str, str] | None = None) -> list[str]:
        """Return the command that would be executed."""
        return ["mock", "run", skill_path]

    async def execute(
        self,
        skill_path: str,
        inputs: dict[str, str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float = 90.0,
        kill_timeout: float = 30.0,
    ) -> CLIExecutionResult:
        """Return the configured mock result."""
        result = self._results.get(skill_path, self._default)
        if result is None:
            skill_id = Path(skill_path).stem
            result = CLIExecutionResult(
                skill_id=skill_id,
                status=ExecutionStatus.SUCCESS,
                exit_code=0,
                stdout="mock stdout",
                stderr="",
                duration_ms=10,
            )
        return result
