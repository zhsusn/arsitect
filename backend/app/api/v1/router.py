"""API v1 top-level router registry."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    advanced,
    annotations,
    applications,
    arch_validation,
    artifacts,
    binding,
    bypass,
    c4,
    canvas_state,
    cli,
    complexity,
    contracts,
    docforge_admin,
    engine,
    execution_plans,
    governance,
    locator,
    monitoring,
    open_ui,
    projects,
    scheduler,
    sketch,
    skill_executions,
    skills,
    stages,
    templates,
    user_stories,
    validation,
    wireframe,
)
from app.core.config import settings

api_router = APIRouter(prefix="/v1")

api_router.include_router(skill_executions.router)
api_router.include_router(applications.router)
api_router.include_router(execution_plans.router)
api_router.include_router(skills.router)
api_router.include_router(stages.router)
api_router.include_router(templates.router)
api_router.include_router(artifacts.router)
api_router.include_router(scheduler.router)
api_router.include_router(complexity.router)
api_router.include_router(advanced.router)
api_router.include_router(governance.router)
api_router.include_router(c4.router)
api_router.include_router(canvas_state.router)
api_router.include_router(monitoring.router)
api_router.include_router(arch_validation.router)
api_router.include_router(bypass.router)
api_router.include_router(open_ui.router)
api_router.include_router(wireframe.router)
api_router.include_router(binding.router)
api_router.include_router(sketch.router)
api_router.include_router(user_stories.router)
api_router.include_router(projects.router)
api_router.include_router(docforge_admin.router)
api_router.include_router(annotations.router)
api_router.include_router(validation.router)
api_router.include_router(contracts.router)
api_router.include_router(engine.router)
api_router.include_router(locator.router)
api_router.include_router(cli.router)


@api_router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }
