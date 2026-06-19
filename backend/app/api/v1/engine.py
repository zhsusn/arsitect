"""Engine router — PocketFlow skill execution."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.common.project_context import ProjectContext
from app.engine.pocketflow_engine import (
    ExecutionResult,
    HTTPAdapter,
    KimiCLIAdapter,
    PocketFlowEngine,
    SkillConfig,
)

router = APIRouter(prefix="/engine", tags=["Execution Engine"])


@router.post("/execute")
async def execute_skill(
    project_id: str,
    skill: SkillConfig,
    adapter: str = "http",
    endpoint: str = "http://localhost:8000/api/v1/health",
) -> dict[str, Any]:
    """Execute a single Skill through PocketFlowEngine.

    Args:
        project_id: Project identifier.
        skill: Skill configuration.
        adapter: "http" or "kimi".
        endpoint: HTTP endpoint when adapter is "http".
    """
    cli_adapter = KimiCLIAdapter() if adapter == "kimi" else HTTPAdapter(endpoint=endpoint)

    with ProjectContext(project_id) as ctx:
        engine = PocketFlowEngine(cli_adapter, ctx)
        result = await engine.execute(skill)
        return _result_to_dict(result)


@router.get("/logs/{skill_id}")
async def get_skill_logs(
    skill_id: str,
    project_id: str,
    limit: int = 10,
) -> dict[str, list[str]]:
    """Get recent skill execution logs."""
    with ProjectContext(project_id) as ctx:
        engine = PocketFlowEngine(KimiCLIAdapter(), ctx, logs_dir=str(ctx.logs_dir))
        logs = await engine.get_logs(skill_id, limit=limit)
        return {"logs": logs}


def _result_to_dict(result: ExecutionResult) -> dict[str, Any]:
    return {
        "skill_id": result.skill_id,
        "status": result.status.value,
        "exit_code": result.exit_code,
        "stdout": result.stdout[:2000],
        "stderr": result.stderr[:2000],
        "output_artifacts": result.output_artifacts,
        "duration_ms": result.duration_ms,
        "log_path": result.log_path,
    }
