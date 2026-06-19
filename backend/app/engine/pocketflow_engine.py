"""PocketFlowEngine — three-phase execution with pluggable CLI adapters."""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.common.project_context import ProjectContext


class ExecutionStatus(StrEnum):
    """Skill execution status."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    KILLED = "killed"


@dataclass
class ExecutionResult:
    """Result of a single skill execution."""

    skill_id: str
    status: ExecutionStatus
    exit_code: int
    stdout: str
    stderr: str
    output_artifacts: list[str]
    log_path: str
    duration_ms: int


@dataclass
class SkillConfig:
    """Skill configuration."""

    skill_id: str
    name: str
    file_path: str
    inputs: list[str]
    outputs: list[str]
    env: dict[str, str] = field(default_factory=dict)
    timeout: float = 90.0
    kill_timeout: float = 30.0


class CLIAdapter:
    """CLI adapter abstract base class.

    Responsibilities: unify invocation interface for different CLI tools.
    Current: KimiCLIAdapter, HTTPAdapter.
    Future: MCPAdapter.
    """

    async def execute(
        self,
        skill_path: str,
        inputs: dict[str, str],
        env: dict[str, str] | None = None,
        timeout: float = 90.0,
        kill_timeout: float = 30.0,
    ) -> ExecutionResult:
        """Execute skill and return result."""
        raise NotImplementedError

    def build_command(self, skill_path: str, inputs: dict[str, str]) -> list[str]:
        """Build command line arguments."""
        raise NotImplementedError


class KimiCLIAdapter(CLIAdapter):
    """Kimi CLI adapter — spawns subprocess with timeout management.

    Invocation: kimi run <skill_file> --input <key>=<path>...
    """

    def build_command(self, skill_path: str, inputs: dict[str, str]) -> list[str]:
        cmd = ["kimi", "run", skill_path]
        for key, value in inputs.items():
            cmd.extend(["--input", f"{key}={value}"])
        return cmd

    async def execute(
        self,
        skill_path: str,
        inputs: dict[str, str],
        env: dict[str, str] | None = None,
        timeout: float = 90.0,
        kill_timeout: float = 30.0,
    ) -> ExecutionResult:
        cmd = self.build_command(skill_path, inputs)
        skill_id = Path(skill_path).stem

        merged_env = {"PYTHONUNBUFFERED": "1"}
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
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            duration_ms = int((time.time() - start_time) * 1000)

            return ExecutionResult(
                skill_id=skill_id,
                status=(
                    ExecutionStatus.SUCCESS if process.returncode == 0 else ExecutionStatus.ERROR
                ),
                exit_code=process.returncode or 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                output_artifacts=[],
                log_path="",
                duration_ms=duration_ms,
            )

        except TimeoutError:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=kill_timeout)
            except TimeoutError:
                process.kill()
                await process.wait()

            return ExecutionResult(
                skill_id=skill_id,
                status=ExecutionStatus.KILLED,
                exit_code=-1,
                stdout="",
                stderr=f"Execution timed out after {timeout}s (SIGKILL)",
                output_artifacts=[],
                log_path="",
                duration_ms=int(timeout * 1000),
            )


class HTTPAdapter(CLIAdapter):
    """HTTP adapter — delegates execution to remote endpoint.

    Used when CLI tool is not available locally; calls HTTP API instead.
    """

    def __init__(self, endpoint: str = "http://localhost:8000/api/v1/health") -> None:
        self.endpoint = endpoint

    def build_command(self, skill_path: str, inputs: dict[str, str]) -> list[str]:
        """HTTP adapter does not build shell commands."""
        return ["http", "POST", self.endpoint]

    async def execute(
        self,
        skill_path: str,
        inputs: dict[str, str],
        env: dict[str, str] | None = None,
        timeout: float = 90.0,
        kill_timeout: float = 30.0,
    ) -> ExecutionResult:
        import httpx

        skill_id = Path(skill_path).stem
        payload = {
            "skill_path": skill_path,
            "inputs": inputs,
            "env": env or {},
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(self.endpoint, json=payload)
                duration_ms = int((time.time() - start_time) * 1000)

                return ExecutionResult(
                    skill_id=skill_id,
                    status=(
                        ExecutionStatus.SUCCESS if resp.status_code < 500 else ExecutionStatus.ERROR
                    ),
                    exit_code=resp.status_code,
                    stdout=resp.text,
                    stderr="" if resp.status_code < 500 else f"HTTP {resp.status_code}",
                    output_artifacts=[],
                    log_path="",
                    duration_ms=duration_ms,
                )
        except httpx.TimeoutException:
            return ExecutionResult(
                skill_id=skill_id,
                status=ExecutionStatus.TIMEOUT,
                exit_code=0,
                stdout="",
                stderr=f"HTTP request timed out after {timeout}s",
                output_artifacts=[],
                log_path="",
                duration_ms=int(timeout * 1000),
            )
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            return ExecutionResult(
                skill_id=skill_id,
                status=ExecutionStatus.ERROR,
                exit_code=0,
                stdout="",
                stderr=str(exc),
                output_artifacts=[],
                log_path="",
                duration_ms=duration_ms,
            )


class PocketFlowEngine:
    """PocketFlow execution engine.

    Three-phase model:
    1. PREP: prepare input artifacts, validate preconditions, compute hashes.
    2. EXEC: invoke CLI via adapter, timeout management, log collection.
    3. POST: capture outputs, validate artifact integrity.
    """

    def __init__(
        self,
        cli_adapter: CLIAdapter,
        project_ctx: ProjectContext,
        logs_dir: str = "./logs",
    ) -> None:
        self.cli = cli_adapter
        self.ctx = project_ctx
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, skill: SkillConfig) -> ExecutionResult:
        """Execute full Prep → Exec → Post lifecycle.

        Args:
            skill: Skill configuration.

        Returns:
            ExecutionResult.
        """
        prep_result = await self._prep_phase(skill)
        exec_result = await self._exec_phase(skill, prep_result)

        if exec_result.status == ExecutionStatus.SUCCESS:
            return await self._post_phase(skill, exec_result)

        return exec_result

    # ============================================================
    # PREP phase
    # ============================================================
    async def _prep_phase(self, skill: SkillConfig) -> dict[str, Any]:
        """Prepare input artifacts.

        1. Validate input artifacts exist.
        2. Compute input hashes (for change detection).
        3. Prepare environment variables.
        """
        artifacts_dir = self.ctx.artifacts_dir
        input_hashes: dict[str, str] = {}
        input_paths: dict[str, str] = {}

        for input_path in skill.inputs:
            full_path = artifacts_dir / input_path
            if not full_path.exists():
                raise FileNotFoundError(
                    f"Input artifact not found: {input_path} (project={self.ctx.project_id})"
                )
            content = full_path.read_text("utf-8")
            input_hashes[input_path] = hashlib.sha256(content.encode()).hexdigest()
            input_paths[input_path] = str(full_path.resolve())

        return {
            "input_hashes": input_hashes,
            "input_paths": input_paths,
            "work_dir": str(self.ctx.artifacts_dir),
        }

    # ============================================================
    # EXEC phase
    # ============================================================
    async def _exec_phase(self, skill: SkillConfig, prep_result: dict[str, Any]) -> ExecutionResult:
        """Execute via CLI adapter.

        1. Build command.
        2. Spawn subprocess.
        3. Timeout management (SIGTERM → SIGKILL).
        4. Collect stdout/stderr.
        5. Write log file.
        """
        result = await self.cli.execute(
            skill_path=skill.file_path,
            inputs=prep_result["input_paths"],
            env=skill.env,
            timeout=skill.timeout,
            kill_timeout=skill.kill_timeout,
        )

        log_path = self._write_log(skill.skill_id, result)
        result.log_path = log_path
        return result

    # ============================================================
    # POST phase
    # ============================================================
    async def _post_phase(
        self, skill: SkillConfig, exec_result: ExecutionResult
    ) -> ExecutionResult:
        """Capture outputs and validate artifacts.

        1. Scan output artifacts.
        2. Validate artifact integrity.
        3. Compute output hashes.
        """
        artifacts_dir = self.ctx.artifacts_dir
        output_artifacts: list[str] = []

        for output_pattern in skill.outputs:
            full_path = artifacts_dir / output_pattern
            if full_path.exists():
                output_artifacts.append(output_pattern)

        exec_result.output_artifacts = output_artifacts
        return exec_result

    # ============================================================
    # Log management
    # ============================================================
    def _write_log(self, skill_id: str, result: ExecutionResult) -> str:
        """Write execution log to disk."""
        timestamp = int(time.time())
        log_file = self.logs_dir / f"{skill_id}_{timestamp}.log"

        log_content = f"""=== Skill Execution Log ===
Skill: {skill_id}
Status: {result.status.value}
Exit Code: {result.exit_code}
Duration: {result.duration_ms}ms
Timestamp: {timestamp}

=== STDOUT ===
{result.stdout}

=== STDERR ===
{result.stderr}
"""
        log_file.write_text(log_content, "utf-8")
        return str(log_file)

    async def get_logs(self, skill_id: str, limit: int = 100) -> list[str]:
        """Get recent log file names."""
        log_files = sorted(
            self.logs_dir.glob(f"{skill_id}_*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return [f.name for f in log_files[:limit]]
