"""DocForge Admin API routes.

Provides endpoints to trigger document standardization pipeline steps
from the Arsitect frontend UI.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4.baseline_store import C4BaselineStore
from app.core.config import settings
from app.docforge.c4_assembler import C4Assembler, C4Workspace
from app.docforge.doc_migration_engine import (
    extract_c4_entities,
    fill_dependencies,
    inject_c4_tags,
    migrate_legacy_docs,
)
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/docforge", tags=["DocForge"])


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------
class MigrateDocsRequest(BaseModel):
    src_root: str = Field(
        default="openspec/changes/sdlc-visualizer",
        description="Relative path from project root to source docs",
    )
    dst_root: str | None = Field(
        default=None,
        description="Output baseline directory (default: src_root/baseline)",
    )


class PipelineRequest(BaseModel):
    src_root: str = Field(
        default="openspec/changes/sdlc-visualizer",
        description="Root directory containing baseline and design docs",
    )
    steps: list[str] = Field(
        default=["migrate", "extract_c4", "inject_tags", "fill_deps"],
        description="Ordered list of steps to execute",
    )


class MigrationResponse(BaseModel):
    success: bool
    migrated: int
    skipped: int
    errors: list[str]


class C4RegistryResponse(BaseModel):
    success: bool
    systems: int
    actors: int
    containers: int
    components: int
    interfaces: int
    registry_path: str


class C4TagResponse(BaseModel):
    success: bool
    modified: int
    skipped: int


class DependencyResponse(BaseModel):
    success: bool
    modified: int
    skipped: int


class StepResult(BaseModel):
    step: str
    success: bool
    detail: dict[str, Any] | None = None
    error: str | None = None


class PipelineResponse(BaseModel):
    success: bool
    results: list[StepResult]
    completed_steps: int
    failed_steps: int


class StatusResponse(BaseModel):
    step: str
    status: str
    progress: float
    message: str


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@router.post("/migrate", response_model=MigrationResponse)
async def migrate_docs_endpoint(req: MigrateDocsRequest) -> MigrationResponse:
    src = settings.project_root / req.src_root
    dst = settings.project_root / req.dst_root if req.dst_root else None
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"Source directory not found: {src}")

    result = await asyncio.to_thread(migrate_legacy_docs, src, dst)
    return MigrationResponse(
        success=len(result.errors) == 0,
        migrated=len(result.migrated),
        skipped=len(result.skipped),
        errors=result.errors,
    )


@router.post("/extract-c4", response_model=C4RegistryResponse)
async def extract_c4_endpoint(req: PipelineRequest) -> C4RegistryResponse:
    src = settings.project_root / req.src_root
    registry = src / "baseline" / "_c4-registry.yaml"
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"Source directory not found: {src}")

    result = await asyncio.to_thread(extract_c4_entities, src, registry)
    return C4RegistryResponse(
        success=True,
        systems=result.systems,
        actors=result.actors,
        containers=result.containers,
        components=result.components,
        interfaces=result.interfaces,
        registry_path=result.registry_path,
    )


@router.post("/inject-c4", response_model=C4TagResponse)
async def inject_c4_endpoint(req: PipelineRequest) -> C4TagResponse:
    baseline = settings.project_root / req.src_root / "baseline"
    registry = baseline / "_c4-registry.yaml"
    if not baseline.exists():
        raise HTTPException(status_code=404, detail=f"Baseline directory not found: {baseline}")
    if not registry.exists():
        raise HTTPException(status_code=404, detail=f"C4 registry not found: {registry}")

    result = await asyncio.to_thread(inject_c4_tags, baseline, registry)
    return C4TagResponse(
        success=True,
        modified=result.modified,
        skipped=result.skipped,
    )


@router.post("/fill-deps", response_model=DependencyResponse)
async def fill_deps_endpoint(req: PipelineRequest) -> DependencyResponse:
    baseline = settings.project_root / req.src_root / "baseline"
    if not baseline.exists():
        raise HTTPException(status_code=404, detail=f"Baseline directory not found: {baseline}")

    result = await asyncio.to_thread(fill_dependencies, baseline)
    return DependencyResponse(
        success=True,
        modified=result.modified,
        skipped=result.skipped,
    )


@router.post("/run-pipeline", response_model=PipelineResponse)
async def run_pipeline_endpoint(req: PipelineRequest) -> PipelineResponse:
    src = settings.project_root / req.src_root
    baseline = src / "baseline"
    registry = baseline / "_c4-registry.yaml"

    results: list[StepResult] = []
    failed = 0

    for step in req.steps:
        if step == "migrate":
            if not src.exists():
                results.append(StepResult(step="migrate", success=False, error="Source not found"))
                failed += 1
                continue
            try:
                res = await asyncio.to_thread(migrate_legacy_docs, src, baseline)
                results.append(StepResult(
                    step="migrate", success=True,
                    detail={"migrated": len(res.migrated), "skipped": len(res.skipped), "errors": res.errors},
                ))
            except Exception as exc:
                results.append(StepResult(step="migrate", success=False, error=str(exc)))
                failed += 1
        elif step == "extract_c4":
            if not src.exists():
                results.append(StepResult(step="extract_c4", success=False, error="Source not found"))
                failed += 1
                continue
            try:
                res = await asyncio.to_thread(extract_c4_entities, src, registry)
                results.append(StepResult(
                    step="extract_c4", success=True,
                    detail={
                        "systems": res.systems, "actors": res.actors, "containers": res.containers,
                        "components": res.components, "interfaces": res.interfaces,
                    },
                ))
            except Exception as exc:
                results.append(StepResult(step="extract_c4", success=False, error=str(exc)))
                failed += 1
        elif step == "inject_tags":
            if not baseline.exists():
                results.append(StepResult(step="inject_tags", success=False, error="Baseline not found"))
                failed += 1
                continue
            if not registry.exists():
                results.append(StepResult(step="inject_tags", success=False, error="Registry not found"))
                failed += 1
                continue
            try:
                res = await asyncio.to_thread(inject_c4_tags, baseline, registry)
                results.append(StepResult(
                    step="inject_tags", success=True,
                    detail={"modified": res.modified, "skipped": res.skipped},
                ))
            except Exception as exc:
                results.append(StepResult(step="inject_tags", success=False, error=str(exc)))
                failed += 1
        elif step == "fill_deps":
            if not baseline.exists():
                results.append(StepResult(step="fill_deps", success=False, error="Baseline not found"))
                failed += 1
                continue
            try:
                res = await asyncio.to_thread(fill_dependencies, baseline)
                results.append(StepResult(
                    step="fill_deps", success=True,
                    detail={"modified": res.modified, "skipped": res.skipped},
                ))
            except Exception as exc:
                results.append(StepResult(step="fill_deps", success=False, error=str(exc)))
                failed += 1
        else:
            results.append(StepResult(step=step, success=False, error=f"Unknown step: {step}"))
            failed += 1

    return PipelineResponse(
        success=failed == 0,
        results=results,
        completed_steps=len([r for r in results if r.success]),
        failed_steps=failed,
    )


@router.get("/pipeline-steps")
async def list_pipeline_steps() -> list[dict[str, str]]:
    return [
        {"key": "migrate", "label": "文档迁移", "description": "将旧文档转换为 YAML Front Matter + 章节锚点"},
        {"key": "extract_c4", "label": "C4 实体提取", "description": "从设计文档提取系统、容器、组件和接口"},
        {"key": "inject_tags", "label": "C4 标签注入", "description": "根据文档层级注入 @C4- 绑定引用标签"},
        {"key": "fill_deps", "label": "依赖填充", "description": "根据默认规则 + 正文引用填充 dependencies 字段"},
    ]


@router.get("/migration-manifest")
async def get_migration_manifest(src_root: str = Query(default="openspec/changes/sdlc-visualizer")) -> dict:
    manifest = settings.project_root / src_root / "baseline" / "_migration-manifest.md"
    if not manifest.exists():
        return {"exists": False, "content": None}
    return {"exists": True, "content": manifest.read_text(encoding="utf-8")}


@router.get("/c4-registry")
async def get_c4_registry(src_root: str = Query(default="openspec/changes/sdlc-visualizer")) -> dict:
    registry = settings.project_root / src_root / "baseline" / "_c4-registry.yaml"
    if not registry.exists():
        return {"exists": False, "content": None}
    return {"exists": True, "content": registry.read_text(encoding="utf-8")}


@router.post("/sync-c4-baseline")
async def sync_c4_baseline(
    req: PipelineRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Sync C4 DSL from baseline files into database."""
    baseline = settings.project_root / req.src_root / "baseline"
    registry_path = baseline / "_c4-registry.yaml"
    if not baseline.exists():
        raise HTTPException(status_code=404, detail=f"Baseline directory not found: {baseline}")
    if not registry_path.exists():
        raise HTTPException(status_code=404, detail=f"C4 registry not found: {registry_path}")

    project_id = Path(req.src_root).name
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))

    workspace = C4Workspace(project_id=project_id)
    systems = registry.get("systems", {})
    if systems:
        first_key = next(iter(systems))
        first_sys = systems[first_key]
        workspace.system = {
            "id": first_key,
            "name": first_sys.get("name", first_key),
        }

    for eid, info in registry.get("actors", {}).items():
        workspace.actors.append({"id": eid, "name": info.get("name", eid)})

    for eid, info in registry.get("containers", {}).items():
        workspace.containers.append({
            "id": eid,
            "name": info.get("name", eid),
            "technology": ", ".join(info.get("aliases", [])),
        })

    for eid, info in registry.get("components", {}).items():
        workspace.components.append({
            "id": eid,
            "name": info.get("name", eid),
            "properties": {},
        })

    for iface in registry.get("interfaces", []):
        workspace.interfaces.append({
            "id": iface["id"],
            "name": f"{iface['method']} {iface['path']}",
            "properties": {"method": iface["method"], "path": iface["path"]},
        })

    # Simple relationships: connect all containers to system
    if workspace.system:
        for c in workspace.containers:
            workspace.relationships.append({
                "source": workspace.system["id"],
                "target": c["id"],
                "description": "contains",
            })

    assembler = C4Assembler()
    dsl_content = assembler.serialize_to_yaml(workspace)

    store = C4BaselineStore(db)
    version = await store.write(
        workspace=workspace,
        dsl_content=dsl_content,
        compiled_from=["docforge_sync"],
    )
    await db.commit()

    return {
        "success": True,
        "project_id": project_id,
        "version": version,
        "elements": {
            "system": 1 if workspace.system else 0,
            "actors": len(workspace.actors),
            "containers": len(workspace.containers),
            "components": len(workspace.components),
            "interfaces": len(workspace.interfaces),
            "relationships": len(workspace.relationships),
        },
    }
