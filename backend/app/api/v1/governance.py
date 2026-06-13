"""Governance router — project lifecycle, complexity and artifact versions."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.health_checker import get_health_checker
from app.common.project_context import ProjectContext
from app.governance.artifact_version_manager import (
    ArtifactVersionManager,
    GitAdapter,
)
from app.governance.complexity_router import (
    ComplexityMetrics,
    ComplexityRouter,
)
from app.governance.project_governance import ProjectGovernance
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/governance", tags=["Governance"])


class ProjectCreateRequest(BaseModel):
    """Request body for creating a project via governance."""

    name: str = Field(..., max_length=64)
    description: str = Field(default="", max_length=256)
    application_id: str = Field(...)
    template_level: str = Field(default="Standard")


class ProjectActivateRequest(BaseModel):
    """Request body for activating a project."""

    complexity_route: str = Field(...)


class ComplexityAssessRequest(BaseModel):
    """Request body for five-dimension complexity assessment."""

    code_lines: int = Field(..., ge=0)
    external_deps: int = Field(..., ge=0)
    data_models: int = Field(..., ge=0)
    api_endpoints: int = Field(..., ge=0)
    business_rules: int = Field(..., ge=0)


class ComplexityAssessResponse(BaseModel):
    """Response for complexity assessment."""

    route: str
    confidence: float
    reasoning: str
    manual_override: bool


class RollbackRequest(BaseModel):
    """Request body for artifact rollback."""

    commit_hash: str


# ============================================================
# Project governance
# ============================================================
@router.post("/projects", status_code=status.HTTP_201_CREATED)
async def create_project(
    req: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Create a new project in Draft state."""
    governance = ProjectGovernance(db)
    project_id = await governance.create(
        name=req.name,
        description=req.description,
        application_id=req.application_id,
        template_level=req.template_level,
    )
    return {"project_id": project_id}


@router.post("/projects/{project_id}/activate")
async def activate_project(
    project_id: str,
    req: ProjectActivateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Activate a Draft project."""
    governance = ProjectGovernance(db)
    await governance.activate(project_id, req.complexity_route)
    return {"project_id": project_id, "status": "active"}


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get project governance details."""
    governance = ProjectGovernance(db)
    project = await governance.get(project_id)
    if project is None:
        raise ValueError(f"Project not found: {project_id}")
    return {
        "project_id": project.id,
        "name": project.name,
        "state": project.state,
        "complexity_route": project.complexity_route,
        "created_at": project.created_at.isoformat() if project.created_at else None,
    }


@router.post("/projects/{project_id}/archive")
async def archive_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Archive an Active project."""
    governance = ProjectGovernance(db)
    await governance.archive(project_id)
    return {"project_id": project_id, "status": "archived"}


@router.post("/projects/{project_id}/cancel")
async def cancel_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Cancel a Draft or Active project."""
    governance = ProjectGovernance(db)
    await governance.cancel(project_id)
    return {"project_id": project_id, "status": "cancelled"}


# ============================================================
# Complexity router
# ============================================================
@router.post("/projects/{project_id}/assess")
async def assess_complexity(
    project_id: str,
    req: ComplexityAssessRequest,
) -> ComplexityAssessResponse:
    """Assess project complexity across five dimensions."""
    router = ComplexityRouter()
    metrics = ComplexityMetrics(
        code_lines=req.code_lines,
        external_deps=req.external_deps,
        data_models=req.data_models,
        api_endpoints=req.api_endpoints,
        business_rules=req.business_rules,
    )
    assessment = router.assess(metrics)
    return ComplexityAssessResponse(
        route=assessment.route.value,
        confidence=assessment.confidence,
        reasoning=assessment.reasoning,
        manual_override=assessment.manual_override,
    )


# ============================================================
# Artifact version manager
# ============================================================
@router.get("/projects/{project_id}/artifacts/{path:path}/history")
async def get_artifact_history(
    project_id: str,
    path: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return Git commit history for an artifact."""
    ctx = ProjectContext(project_id)
    manager = ArtifactVersionManager(GitAdapter(), ctx)
    history = await manager.get_history(path, limit=limit)
    return [
        {
            "commit_hash": h.commit_hash,
            "message": h.message,
            "author": h.author,
            "timestamp": h.timestamp.isoformat() if h.timestamp else None,
            "files_changed": h.files_changed,
        }
        for h in history
    ]


@router.post("/projects/{project_id}/artifacts/{path:path}/rollback")
async def rollback_artifact(
    project_id: str,
    path: str,
    req: RollbackRequest,
) -> dict[str, Any]:
    """Rollback an artifact to a specific Git commit."""
    ctx = ProjectContext(project_id)
    manager = ArtifactVersionManager(GitAdapter(), ctx)
    ok = await manager.rollback(path, req.commit_hash)
    return {"success": ok, "file_path": path, "commit_hash": req.commit_hash}


# ============================================================
# Health checker
# ============================================================
@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Return health status of all registered dependency services."""
    health_checker = get_health_checker()
    statuses = health_checker.get_all_statuses()
    return {
        "services": {
            name: {
                "status": result.status.value,
                "latency_ms": result.latency_ms,
                "message": result.message,
                "last_checked": result.last_checked,
            }
            for name, result in statuses.items()
        }
    }


@router.get("/health/{service}")
async def service_health(service: str) -> dict[str, Any]:
    """Return health status for a single service."""
    health_checker = get_health_checker()
    status = health_checker.get_status(service)
    result = health_checker.get_all_statuses().get(service)
    return {
        "service": service,
        "status": status.value,
        "latency_ms": result.latency_ms if result else None,
        "message": result.message if result else None,
        "last_checked": result.last_checked if result else None,
    }
