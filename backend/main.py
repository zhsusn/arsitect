"""SDLC Visualizer — FastAPI application entry point."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.c4.baseline_store import C4BaselineStore
from app.common.event_bus import get_event_bus
from app.common.file_system_watcher import get_file_system_watcher
from app.common.health_checker import (
    HealthChecker,
    get_health_checker,
)
from app.core.config import settings
from app.core.exceptions import AppError, app_error_handler, generic_exception_handler
from app.core.logging import setup_logging
from app.infrastructure.database.session import AsyncSessionLocal, init_db


async def _c4_sync_loop() -> None:
    """Background task: periodically scan filesystem baseline and sync to DB."""
    changes_dir = settings.project_root / "openspec" / "changes"
    while True:
        try:
            await asyncio.sleep(60)
            if not changes_dir.is_dir():
                continue
            async with AsyncSessionLocal() as db:
                store = C4BaselineStore(db)
                for baseline_dir in changes_dir.iterdir():
                    if baseline_dir.is_dir() and (baseline_dir / "baseline" / "_c4-registry.yaml").exists():
                        await store.sync_from_filesystem(baseline_dir.name)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[C4Sync] Background sync error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    setup_logging()
    await init_db()
    await get_event_bus().start()

    # Start dependency health monitoring
    health_checker = get_health_checker()
    if settings.OPENUI_HEALTH_CHECK_ENABLED:
        health_checker.register("openui", HealthChecker.check_openui)
    health_checker.register("git", HealthChecker.check_git)
    health_checker.register("docker", HealthChecker.check_docker)
    health_checker.register("kimi-cli", HealthChecker.check_kimi_cli)
    await health_checker.start_monitoring()

    sync_task = asyncio.create_task(_c4_sync_loop())
    try:
        yield
    finally:
        sync_task.cancel()
        with suppress(asyncio.CancelledError):
            await sync_task
        await health_checker.stop()
        get_file_system_watcher().stop_all()
        await get_event_bus().stop()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-driven software lifecycle management platform.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)
