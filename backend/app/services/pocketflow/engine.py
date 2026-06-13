"""PocketFlow engine: three-phase pipeline orchestrator."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from app.services.pocketflow.exec_stage import ExecStage
from app.services.pocketflow.lock_manager import LockManager
from app.services.pocketflow.log_collector import LogCollector, LogLevel
from app.services.pocketflow.post_stage import PostStage
from app.services.pocketflow.prep_stage import PrepStage
from app.services.pocketflow.state_machine import ExecutionStatus, SkillExecutionStateMachine


@dataclass
class PhaseResult:
    """Result for a single phase."""

    status: str
    duration_ms: int
    error_msg: str | None = None
    output_artifacts: list[str] | None = None


@dataclass
class PocketFlowResult:
    """Overall PocketFlow execution result."""

    execution_id: str
    final_status: str
    phase_results: dict[str, PhaseResult] = field(default_factory=dict)
    missing_artifacts: list[str] = field(default_factory=list)


class PocketFlowEngine:
    """Orchestrate Prep → Exec → Post pipeline."""

    def __init__(
        self,
        prep: PrepStage | None = None,
        exec_: ExecStage | None = None,
        post: PostStage | None = None,
        lock_manager: LockManager | None = None,
    ) -> None:
        """Initialize with stage services."""
        self._prep = prep or PrepStage()
        self._exec = exec_ or ExecStage()
        self._post = post or PostStage()
        self._lock_manager = lock_manager or LockManager()

    async def execute(
        self,
        skill_path: str,
        project_id: str,
        work_dir: str,
        expected_artifacts: list[str] | None = None,
        endpoint: str = "http://localhost:8000/api/v1/health",
    ) -> PocketFlowResult:
        """Execute full Prep → Exec → Post lifecycle.

        Args:
            skill_path: Path to SKILL.md.
            project_id: Project ID.
            work_dir: Working directory.
            expected_artifacts: Expected output artifacts.
            endpoint: Mock endpoint for exec stage.

        Returns:
            PocketFlowResult with all phase results.
        """
        execution_id = str(uuid.uuid4())
        sm = SkillExecutionStateMachine(ExecutionStatus.NOT_STARTED)
        logs = LogCollector()
        result = PocketFlowResult(execution_id=execution_id, final_status="FAILED")

        await self._lock_manager.acquire(project_id)
        try:
            # Prep
            sm.transition(ExecutionStatus.PREPARING)
            logs.log("prep", LogLevel.INFO, "Starting prep stage")
            prep_start = time.time()
            prep_result = await self._prep.prepare(skill_path, project_id)
            prep_duration = int((time.time() - prep_start) * 1000)

            if not prep_result.success:
                sm.transition(ExecutionStatus.PREP_FAILED)
                logs.log("prep", LogLevel.ERROR, f"Prep failed: {prep_result.error}")
                result.phase_results["prep"] = PhaseResult(
                    status="FAILED",
                    duration_ms=prep_duration,
                    error_msg=prep_result.error,
                )
                return result

            sm.transition(ExecutionStatus.PREP_COMPLETED)
            logs.log("prep", LogLevel.INFO, "Prep completed")
            result.phase_results["prep"] = PhaseResult(
                status="PASSED",
                duration_ms=prep_duration,
            )

            # Exec
            sm.transition(ExecutionStatus.EXECUTING)
            logs.log("exec", LogLevel.INFO, "Starting exec stage")
            exec_start = time.time()
            exec_result = await self._exec.execute(
                endpoint,
                {"skill_path": skill_path, "project_id": project_id},
            )
            exec_duration = int((time.time() - exec_start) * 1000)

            if not exec_result.success:
                sm.transition(ExecutionStatus.EXEC_FAILED)
                logs.log("exec", LogLevel.ERROR, f"Exec failed: {exec_result.error}")
                result.phase_results["exec"] = PhaseResult(
                    status="FAILED",
                    duration_ms=exec_duration,
                    error_msg=exec_result.error,
                )
                return result

            sm.transition(ExecutionStatus.EXEC_COMPLETED)
            logs.log("exec", LogLevel.INFO, "Exec completed")
            result.phase_results["exec"] = PhaseResult(
                status="PASSED",
                duration_ms=exec_duration,
            )

            # Post
            sm.transition(ExecutionStatus.POST_PROCESSING)
            logs.log("post", LogLevel.INFO, "Starting post stage")
            post_start = time.time()
            post_result = await self._post.finalize(
                expected_artifacts or [],
                work_dir,
            )
            post_duration = int((time.time() - post_start) * 1000)

            if not post_result.success:
                sm.transition(ExecutionStatus.POST_FAILED)
                logs.log("post", LogLevel.ERROR, f"Post failed: {post_result.error}")
                result.phase_results["post"] = PhaseResult(
                    status="FAILED",
                    duration_ms=post_duration,
                    error_msg=post_result.error,
                    output_artifacts=post_result.artifacts,
                )
                result.missing_artifacts = [
                    w["artifact_path"]
                    for w in post_result.report.warnings
                    if w["warning_type"] == "MISSING_REQUIRED"
                ]
                return result

            sm.transition(ExecutionStatus.COMPLETED)
            logs.log("post", LogLevel.INFO, "Post completed")
            result.phase_results["post"] = PhaseResult(
                status="PASSED",
                duration_ms=post_duration,
                output_artifacts=post_result.artifacts,
            )
            result.final_status = "PASSED"

        finally:
            self._lock_manager.release(project_id)

        return result
