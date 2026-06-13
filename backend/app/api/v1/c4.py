"""C4 architecture router — DSL CRUD and AI generation."""

from __future__ import annotations

import asyncio
from datetime import UTC
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4 import registry_extractor
from app.c4.baseline_store import C4BaselineStore
from app.c4.dsl_manager import C4DSLManager, DSLEditDTO
from app.c4.governance_fix.llm_gateway import get_llm_gateway
from app.c4.governance_fix.models import GovernanceIssue, RootCause
from app.c4.governance_fix.planner import FixPlanner
from app.c4.registry_extractor import extract_registry as run_c4_extraction
from app.c4.renderer import C4Renderer
from app.infrastructure.database.session import get_db
from app.schemas.c4 import (
    C4AnalyzeResponseDTO,
    C4ChangeSetDTO,
    C4DiffItemDTO,
    C4DSLVersionDTO,
    C4ExtractResponseDTO,
    C4FixPlanItemDTO,
    C4FixPlanRequestDTO,
    C4FixPlanResponseDTO,
    C4LevelAnalysisDTO,
    C4OptimizeChangeRequestDTO,
    C4OptimizeChangeResponseDTO,
    C4OrphanComponentDTO,
    C4OrphanToggleResponseDTO,
    C4RegistryDiffDTO,
    C4RegistryStatsDTO,
    C4RelationshipTupleDTO,
    C4RenderResponseDTO,
    C4SketchResponseDTO,
    C4WireframeResponseDTO,
)
from app.schemas.c4 import (
    DSLEditDTO as DSLEditDTOSch,
)

router = APIRouter(tags=["c4"])


# ============================================================
# Unified C4 DSL endpoints (arsitect.aac.yml)
# ============================================================

async def get_baseline_store(
    db: AsyncSession = Depends(get_db),
) -> C4BaselineStore:
    return C4BaselineStore(db)


async def get_dsl_manager(
    store: C4BaselineStore = Depends(get_baseline_store),
) -> C4DSLManager:
    return C4DSLManager(store)


async def get_renderer(
    dsl: C4DSLManager = Depends(get_dsl_manager),
) -> C4Renderer:
    return C4Renderer(dsl)


@router.get("/c4/dsl/current")
async def get_current_dsl(
    project_id: str,
    dsl: C4DSLManager = Depends(get_dsl_manager),
) -> dict[str, str]:
    """Get current unified DSL."""
    content = await dsl.read_current(project_id)
    if not content:
        raise HTTPException(404, "No C4 DSL found for this project")
    return {"content": content, "format": "yaml"}


@router.post("/c4/dsl/edit")
async def edit_dsl(
    project_id: str,
    dto: DSLEditDTOSch,
    dsl: C4DSLManager = Depends(get_dsl_manager),
) -> dict[str, str]:
    """Edit DSL (creates new version)."""
    version = await dsl.edit(
        project_id,
        DSLEditDTO(content=dto.content, edit_reason=dto.edit_reason, editor=dto.editor),
    )
    return {"version": version, "message": "DSL updated successfully"}


@router.get("/c4/dsl/versions")
async def list_dsl_versions(
    project_id: str,
    dsl: C4DSLManager = Depends(get_dsl_manager),
) -> dict[str, list[C4DSLVersionDTO]]:
    """List all DSL versions."""
    versions = await dsl.list_versions(project_id)
    return {"versions": [C4DSLVersionDTO(**v) for v in versions]}


@router.post("/c4/dsl/rollback")
async def rollback_dsl(
    project_id: str,
    version: str,
    dsl: C4DSLManager = Depends(get_dsl_manager),
) -> dict[str, str]:
    """Rollback to specified version."""
    result = await dsl.rollback(project_id, version)
    return {"version": result}


@router.get("/c4/render")
async def render_c4(
    project_id: str,
    level: str = "L2",
    refresh: bool = Query(default=False, description="Re-extract from design docs and sync to DB before rendering"),
    expanded: str | None = Query(default=None, description="Comma-separated list of container IDs to expand in L3 view. Empty = all collapsed, omitted = all expanded."),
    renderer: C4Renderer = Depends(get_renderer),
    store: C4BaselineStore = Depends(get_baseline_store),
) -> C4RenderResponseDTO:
    """Render C4 architecture as Mermaid.

    Set refresh=1 to force re-extract C4 relationships from design documents
    and sync to database before rendering.

    For L3 view, use `expanded` to control container folding:
    - omitted or empty string in query: all containers expanded (backward compatible)
    - `expanded=` (explicit empty): all containers collapsed
    - `expanded=backend-api,frontend-spa`: expand specified containers only
    """
    if refresh:
        await asyncio.to_thread(run_c4_extraction, project_id)
        await store.sync_from_filesystem(project_id)

    # Parse expanded containers for L3 folding
    expanded_containers: list[str] | None = None
    print(f"[C4 DEBUG] raw expanded param: {repr(expanded)}")
    if expanded is not None:
        stripped = expanded.strip()
        if stripped == "":
            # Explicit empty string means all collapsed
            expanded_containers = []
        else:
            expanded_containers = [c.strip() for c in stripped.split(",") if c.strip()]
    print(f"[C4 DEBUG] parsed expanded_containers: {expanded_containers}")
    # If expanded param is completely absent (None), it stays None (all expanded)

    result = await renderer.render(project_id, level, expanded_containers)
    debug_info = f"raw_expanded={repr(expanded)}, parsed={expanded_containers}, first_line={result.mermaid_code.split(chr(10))[0]}"
    print(f"[C4 DEBUG] {debug_info}")
    return C4RenderResponseDTO(
        mermaid_code=result.mermaid_code,
        view_level=result.view_level,
        node_count=result.node_count,
        edge_count=result.edge_count,
        debug_info=debug_info,
        analysis_report=result.analysis_report,
        consistency_report=result.consistency_report,
    )


def _stats_from_registry(project_id: str, content: dict[str, Any] | None) -> C4RegistryStatsDTO:
    """Build a stats DTO from a registry dictionary."""
    data = {
        "systems": 0,
        "actors": 0,
        "containers": 0,
        "components": 0,
        "interfaces": 0,
        "relationships": 0,
    }
    if not content:
        return C4RegistryStatsDTO(project_id=project_id, orphans=[], **data)

    data = {
        "systems": len(content.get("systems", {})),
        "actors": len(content.get("actors", {})),
        "containers": len(content.get("containers", {})),
        "components": len(content.get("components", {})),
        "interfaces": len(content.get("interfaces", [])),
        "relationships": len(content.get("relationships", [])),
    }
    components = content.get("components", {})
    rel_nodes = set()
    for rel in content.get("relationships", []):
        rel_nodes.add(rel.get("source", ""))
        rel_nodes.add(rel.get("target", ""))
    orphans = [
        C4OrphanComponentDTO(
            id=cid,
            name=info.get("name", cid),
            container_id=info.get("container_id"),
            source=info.get("source", "doc"),
            implemented=bool(info.get("implemented", False)),
            intentional_orphan=bool(info.get("intentional_orphan", False)),
            source_file=info.get("source_file") or info.get("source_code_file"),
        )
        for cid, info in components.items()
        if cid not in rel_nodes
    ]
    intentional = [o for o in orphans if o.id in components and components[o.id].get("intentional_orphan")]
    return C4RegistryStatsDTO(
        project_id=project_id,
        orphans=orphans,
        intentional_orphan_count=len(intentional),
        effective_orphan_count=len(orphans) - len(intentional),
        orphan_count=len(orphans),
        **data,
    )


@router.post("/c4/registry/extract")
async def extract_c4_registry(
    project_id: str,
    store: C4BaselineStore = Depends(get_baseline_store),
) -> C4ExtractResponseDTO:
    """Run the C4 registry extractor, sync the DSL baseline and return statistics."""
    try:
        stats_dict = await asyncio.to_thread(registry_extractor.extract_registry, project_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"C4 extraction failed: {exc}") from exc

    await store.sync_from_filesystem(project_id)

    stats = C4RegistryStatsDTO(**stats_dict)
    return C4ExtractResponseDTO(
        project_id=project_id,
        message=f"Registry extracted: {stats.components} components, {stats.relationships} relationships",
        stats=stats,
    )


@router.get("/c4/registry/stats")
async def get_c4_registry_stats(
    project_id: str,
) -> C4RegistryStatsDTO:
    """Return the latest C4 registry statistics without re-extracting."""
    registry = await asyncio.to_thread(registry_extractor.load_registry, project_id)
    return _stats_from_registry(project_id, registry)


@router.get("/c4/registry/diff")
async def get_c4_registry_diff(
    project_id: str,
    since: str,
) -> C4RegistryDiffDTO:
    """Compare the current registry to the latest snapshot at or before ``since``.

    ``since`` must be an ISO-8601 timestamp (e.g. ``2026-06-12T10:00:00Z``).
    """
    from datetime import datetime

    try:
        since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(400, f"Invalid since timestamp: {exc}") from exc

    current = await asyncio.to_thread(registry_extractor.load_registry, project_id)
    if current is None:
        raise HTTPException(404, "Current registry not found")

    snapshot_path = await asyncio.to_thread(
        registry_extractor.find_snapshot_at_or_before, project_id, since_dt.astimezone(UTC)
    )
    previous = None
    if snapshot_path:
        previous = await asyncio.to_thread(registry_extractor.load_registry, project_id)
        # load_registry always returns the current registry; load the snapshot explicitly
        import yaml

        previous = yaml.safe_load(snapshot_path.read_text(encoding="utf-8"))

    # Compute stats for orphan counts
    current_stats = _stats_from_registry(project_id, current)
    previous_stats = _stats_from_registry(project_id, previous)

    diff = registry_extractor.compute_registry_diff(
        {"stats": current_stats.model_dump(), **current},
        {"stats": previous_stats.model_dump(), **(previous or {})},
    )

    return C4RegistryDiffDTO(
        project_id=project_id,
        since=since,
        components_added=diff["components"]["added"],
        components_removed=diff["components"]["removed"],
        components_changed=[
            C4DiffItemDTO(id=item["id"], before=item["before"], after=item["after"])
            for item in diff["components"]["changed"]
        ],
        relationships_added=[
            C4RelationshipTupleDTO(source=s, target=t, description=d)
            for s, t, d in diff["relationships"]["added"]
        ],
        relationships_removed=[
            C4RelationshipTupleDTO(source=s, target=t, description=d)
            for s, t, d in diff["relationships"]["removed"]
        ],
        orphan_count_before=diff["orphan_delta"]["before"],
        orphan_count_after=diff["orphan_delta"]["after"],
        components_before=diff["counts"]["before"]["components"],
        components_after=diff["counts"]["after"]["components"],
        relationships_before=diff["counts"]["before"]["relationships"],
        relationships_after=diff["counts"]["after"]["relationships"],
    )


@router.post("/c4/registry/orphans/{component_id}/intentional")
async def toggle_intentional_orphan(
    project_id: str,
    component_id: str,
) -> C4OrphanToggleResponseDTO:
    """Toggle the intentional orphan flag for a registry component."""
    try:
        new_value = await asyncio.to_thread(
            registry_extractor.toggle_intentional_orphan, project_id, component_id
        )
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    return C4OrphanToggleResponseDTO(
        project_id=project_id,
        component_id=component_id,
        intentional_orphan=new_value,
    )


@router.get("/c4/analyze")
async def analyze_c4(
    project_id: str,
    renderer: C4Renderer = Depends(get_renderer),
) -> C4AnalyzeResponseDTO:
    """Run full architecture governance analysis across L1-L4.

    Returns structural issues per level plus design-to-code consistency report.
    Does not generate Mermaid diagrams.
    """
    level_results = await renderer.analyze_all(project_id)

    # Run consistency check on L2 (covers containers ↔ code directories)
    workspace = await renderer.dsl.read_workspace(project_id)
    consistency_data = None
    if workspace:
        try:
            from app.c4.code_scanner import CodeScanner
            from app.c4.consistency_checker import ConsistencyChecker

            checker = ConsistencyChecker(CodeScanner())
            consistency = checker.check(workspace, "L2")
            consistency_data = consistency.to_dict()
        except Exception:
            pass

    overall_passed = all(r.get("passed", True) for r in level_results)
    if consistency_data and not consistency_data.get("passed", True):
        overall_passed = False

    return C4AnalyzeResponseDTO(
        project_id=project_id,
        overall_passed=overall_passed,
        levels=[
            C4LevelAnalysisDTO(
                level=r["level"],
                passed=r["passed"],
                issues=r["issues"],
                summary=r["summary"],
            )
            for r in level_results
        ],
        consistency=consistency_data,
    )


@router.post("/c4/governance/fix-plan")
async def generate_c4_fix_plan(
    project_id: str,
    req: C4FixPlanRequestDTO,
    dsl: C4DSLManager = Depends(get_dsl_manager),
) -> C4FixPlanResponseDTO:
    """Generate a preview-only fix plan for the submitted C4 governance issues.

    The plan selects the best strategy per issue and returns concrete ChangeSets.
    Changes are NOT applied automatically; they are meant for human review.
    """
    content = await dsl.read_current(project_id)
    workspace_model: dict[str, Any] = yaml.safe_load(content) if content else {}
    registry = await asyncio.to_thread(registry_extractor.load_registry, project_id) or {}

    code_entities = [
        {
            "name": cid,
            "file_path": info.get("source_file") or info.get("source_code_file", ""),
            "container_hint": info.get("container_id", ""),
        }
        for cid, info in registry.get("components", {}).items()
    ]

    context = dict(req.context or {})
    context.setdefault("workspace_model", workspace_model)
    context.setdefault("registry", registry)
    context.setdefault("code_entities", code_entities)

    # Optional LLM root-cause analysis driven by the user's strategy prompt.
    strategy_prompt = context.get("strategy_prompt", "")
    root_cause_analysis = ""
    if strategy_prompt:
        issues_text = "\n".join(
            f"- [{issue.severity}] {issue.rule_id}: {issue.message} "
            f"(fix_hint: {issue.fix_hint or 'none'}, fix_action: {issue.fix_action or 'none'})"
            for issue in req.issues
        )
        analysis_prompt = (
            f"{strategy_prompt}\n\n"
            f"Project: {project_id}\n"
            f"Selected governance issues:\n{issues_text}\n\n"
            "Please analyze the root causes of the issues above and summarize how they should be fixed. "
            "Keep the analysis concise and actionable."
        )
        try:
            llm = get_llm_gateway()
            root_cause_analysis = await llm.generate(analysis_prompt)
        except Exception as exc:  # noqa: BLE001
            root_cause_analysis = f"（根因分析未能完成：{exc}）"
        context["root_cause_analysis"] = root_cause_analysis

    def _infer_root_cause(rule_id: str, fix_action: str, fix_hint: str) -> str:
        # Normalize prefixed rule ids so the same logic applies to the analyzer
        # output (e.g. "C4-ORPHAN-001") and legacy ids (e.g. "ORPHAN-001").
        bare_rule = rule_id.removeprefix("C4-")

        if fix_action == "UPDATE_CODE":
            return RootCause.CODE_MISSING
        if fix_action == "UPDATE_DOC":
            return RootCause.DOC_INCOMPLETE
        if fix_action == "BOTH":
            return RootCause.DOC_CODE_MISMATCH

        if rule_id in ("CON-C2F-001",) or "代码中未找到" in fix_hint:
            return RootCause.CODE_MISSING
        if rule_id in ("CON-F2C-001",) or "DSL 中未定义" in fix_hint:
            return RootCause.DOC_INCOMPLETE
        if rule_id.startswith("IMP-"):
            if fix_action == "UPDATE_DOC" or "缺少" in fix_hint:
                return RootCause.DSL_MISSING_RELATIONSHIP
            if fix_action == "UPDATE_CODE" or "未授权" in fix_hint:
                return RootCause.CODE_UNDESIGNED_RELATIONSHIP
            return RootCause.RELATIONSHIP_MISSING
        if bare_rule in ("ORPHAN-001", "ORPHAN-002") or "孤立" in fix_hint:
            if bare_rule == "ORPHAN-002" or "intentional" in fix_hint.lower():
                return RootCause.INTENTIONAL_DESIGN
            return RootCause.CODE_DEAD
        if rule_id in ("C4-NAME-001", "C4-LEVEL-001"):
            return RootCause.DOC_NON_COMPLIANT
        if rule_id in ("C4-DISCONN-001",):
            return RootCause.RELATIONSHIP_MISSING
        if rule_id == "CON-M2C-001":
            return RootCause.DOC_INCOMPLETE
        if rule_id == "CON-C2M-001":
            return RootCause.CODE_MISSING
        return RootCause.UNKNOWN

    issues: list[GovernanceIssue] = []
    for issue in req.issues:
        data = issue.model_dump()
        if not data.get("root_cause") or data["root_cause"] == RootCause.UNKNOWN:
            data["root_cause"] = _infer_root_cause(
                data.get("rule_id", ""),
                data.get("fix_action", ""),
                data.get("fix_hint", ""),
            )
        issues.append(GovernanceIssue(**data))

    planner = FixPlanner()
    plans = await planner.plan(issues, project_id, context)

    # If the LLM produced a root-cause analysis, prepend it to each rationale
    # so the user can see the reasoning behind the proposed changes.
    if root_cause_analysis:
        for plan in plans:
            for change in plan.changes:
                change.rationale = (
                    f"【根因分析】\n{root_cause_analysis}\n\n"
                    f"【修复方案】\n{change.rationale}"
                )

    return C4FixPlanResponseDTO(
        project_id=project_id,
        plans=[
            C4FixPlanItemDTO(
                issue_ids=p.issue_ids,
                changes=[
                    C4ChangeSetDTO(
                        action=c.action,
                        target_path=c.target_path,
                        before=c.before,
                        after=c.after,
                        rationale=c.rationale,
                        risk_level=c.risk_level,
                        auto_applicable=c.auto_applicable,
                        requires_confirmation=c.requires_confirmation,
                        issue_id=c.issue_id,
                    )
                    for c in p.changes
                ],
                dry_run=p.dry_run,
            )
            for p in plans
        ],
        analysis=root_cause_analysis,
        strategy_prompt=strategy_prompt,
    )


@router.post("/c4/governance/optimize-change")
async def optimize_c4_change(
    project_id: str,
    req: C4OptimizeChangeRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> C4OptimizeChangeResponseDTO:
    """Optimize a single fix plan change using AI.

    Returns the change with an improved ``after`` content based on the prompt.
    """
    from app.services.arch_governance_service import ArchGovernanceService

    svc = ArchGovernanceService(db)
    optimized = await svc.optimize_change(
        project_id=project_id,
        prompt=req.prompt,
        change=req.change.model_dump(),
    )
    return C4OptimizeChangeResponseDTO(change=C4ChangeSetDTO(**optimized))


@router.get("/c4/wireframe")
async def generate_wireframe(
    project_id: str,
    store: C4BaselineStore = Depends(get_baseline_store),
) -> C4WireframeResponseDTO:
    """Generate wireframe SVG with page graph."""
    from app.c4.wireframe_engine import WireframeEngine

    engine = WireframeEngine(store)
    result = await engine.generate(project_id)
    return C4WireframeResponseDTO(
        svg=result.svg_content,
        page_count=len(result.pages),
        edge_count=len(result.edges),
        orphan_pages=result.orphan_pages,
        pages=[
            {"id": p.page_id, "title": p.title, "type": p.page_type}
            for p in result.pages
        ],
    )


@router.get("/c4/sketch")
async def generate_sketch(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> C4SketchResponseDTO:
    """Generate navigable HTML sketch."""
    from app.c4.sketch_generator import SketchGenerator
    from app.docforge.fragment_registry import FragmentRegistry

    generator = SketchGenerator(FragmentRegistry(db))
    html = await generator.generate(project_id)
    return C4SketchResponseDTO(html=html, format="html")
