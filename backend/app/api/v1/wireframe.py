"""Wireframe router — CRUD + generation for wireframes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.schemas.wireframe import (
    WireframeCreateDTO,
    WireframeGenerateDTO,
    WireframeResponseDTO,
    WireframeUpdateDTO,
)
from app.schemas.wireframe_nav_link import WireframeNavLinkResponseDTO
from app.schemas.wireframe_page import (
    WireframePageCreateDTO,
    WireframePageResponseDTO,
    WireframePageUpdateDTO,
)
from app.services.wireframe_nav_link_service import WireframeNavLinkService
from app.services.wireframe_page_service import WireframePageService
from app.services.wireframe_service import WireframeService

router = APIRouter(tags=["wireframes"])


# ------------------------------------------------------------------
# Wireframe session endpoints
# ------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/wireframes",
    response_model=WireframeResponseDTO,
    status_code=201,
)
async def create_wireframe(
    project_id: str,
    dto: WireframeCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> WireframeResponseDTO:
    """Create a new wireframe session."""
    svc = WireframeService(db)
    wf = await svc.create_wireframe(
        project_id=project_id,
        name=dto.name,
        status=dto.status,
    )
    return WireframeResponseDTO(
        wireframe_id=wf.wireframe_id,
        project_id=wf.project_id,
        name=wf.name,
        c4_baseline_version=wf.c4_baseline_version,
        pipeline_stage=wf.pipeline_stage,
        page_count=wf.page_count,
        avg_confidence=wf.avg_confidence,
        status=wf.status,
        created_at=wf.created_at,
        updated_at=wf.updated_at,
    )


@router.post(
    "/projects/{project_id}/wireframes/generate",
    response_model=WireframeResponseDTO,
    status_code=201,
)
async def generate_wireframe(
    project_id: str,
    dto: WireframeGenerateDTO,
    db: AsyncSession = Depends(get_db),
) -> WireframeResponseDTO:
    """Generate wireframe pages from C4 DSL."""
    svc = WireframeService(db)
    wf = await svc.generate_from_c4(project_id=project_id)
    return WireframeResponseDTO(
        wireframe_id=wf.wireframe_id,
        project_id=wf.project_id,
        name=wf.name,
        c4_baseline_version=wf.c4_baseline_version,
        pipeline_stage=wf.pipeline_stage,
        page_count=wf.page_count,
        avg_confidence=wf.avg_confidence,
        status=wf.status,
        created_at=wf.created_at,
        updated_at=wf.updated_at,
    )


@router.get(
    "/projects/{project_id}/wireframes",
    response_model=list[WireframeResponseDTO],
)
async def list_wireframes(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[WireframeResponseDTO]:
    """List wireframes for a project."""
    svc = WireframeService(db)
    wfs = await svc.list_wireframes(project_id)
    return [
        WireframeResponseDTO(
            wireframe_id=w.wireframe_id,
            project_id=w.project_id,
            name=w.name,
            c4_baseline_version=w.c4_baseline_version,
            pipeline_stage=w.pipeline_stage,
            page_count=w.page_count,
            avg_confidence=w.avg_confidence,
            status=w.status,
            created_at=w.created_at,
            updated_at=w.updated_at,
        )
        for w in wfs
    ]


@router.get(
    "/wireframes/{wireframe_id}",
    response_model=WireframeResponseDTO,
)
async def get_wireframe(
    wireframe_id: str,
    db: AsyncSession = Depends(get_db),
) -> WireframeResponseDTO:
    """Get a wireframe session by ID."""
    svc = WireframeService(db)
    wf = await svc.get_wireframe(wireframe_id)
    return WireframeResponseDTO(
        wireframe_id=wf.wireframe_id,
        project_id=wf.project_id,
        name=wf.name,
        c4_baseline_version=wf.c4_baseline_version,
        pipeline_stage=wf.pipeline_stage,
        page_count=wf.page_count,
        avg_confidence=wf.avg_confidence,
        status=wf.status,
        created_at=wf.created_at,
        updated_at=wf.updated_at,
    )


@router.patch(
    "/wireframes/{wireframe_id}",
    response_model=WireframeResponseDTO,
)
async def update_wireframe(
    wireframe_id: str,
    dto: WireframeUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> WireframeResponseDTO:
    """Update a wireframe session."""
    svc = WireframeService(db)
    wf = await svc.update_wireframe(wireframe_id, dto.model_dump(exclude_unset=True))
    return WireframeResponseDTO(
        wireframe_id=wf.wireframe_id,
        project_id=wf.project_id,
        name=wf.name,
        c4_baseline_version=wf.c4_baseline_version,
        pipeline_stage=wf.pipeline_stage,
        page_count=wf.page_count,
        avg_confidence=wf.avg_confidence,
        status=wf.status,
        created_at=wf.created_at,
        updated_at=wf.updated_at,
    )


@router.delete(
    "/wireframes/{wireframe_id}",
    status_code=204,
    response_model=None,
)
async def delete_wireframe(
    wireframe_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a wireframe session."""
    svc = WireframeService(db)
    await svc.delete_wireframe(wireframe_id)


# ------------------------------------------------------------------
# Wireframe page endpoints
# ------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/wireframe-pages",
    response_model=WireframePageResponseDTO,
    status_code=201,
)
async def create_wireframe_page(
    project_id: str,
    dto: WireframePageCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> WireframePageResponseDTO:
    """Create a wireframe page."""
    svc = WireframePageService(db)
    page = await svc.create_page(
        wireframe_id=dto.wireframe_id,
        project_id=project_id,
        entity_id=dto.entity_id,
        entity_name=dto.entity_name,
        page_name=dto.page_name,
        page_type=dto.page_type,
        confidence=dto.confidence,
        mapping_source=dto.mapping_source,
        svg_content=dto.svg_content,
        layout_json=dto.layout_json,
        status=dto.status,
        sort_order=dto.sort_order,
    )
    return WireframePageResponseDTO(
        page_id=page.page_id,
        wireframe_id=page.wireframe_id,
        project_id=page.project_id,
        entity_id=page.entity_id,
        entity_name=page.entity_name,
        page_name=page.page_name,
        page_type=page.page_type,
        confidence=page.confidence,
        mapping_source=page.mapping_source,
        svg_content=page.svg_content,
        layout_json=page.layout_json,
        status=page.status,
        sort_order=page.sort_order,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


@router.get(
    "/projects/{project_id}/wireframe-pages",
    response_model=list[WireframePageResponseDTO],
)
async def list_wireframe_pages(
    project_id: str,
    wireframe_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[WireframePageResponseDTO]:
    """List wireframe pages for a project."""
    svc = WireframePageService(db)
    pages = await svc.list_pages(project_id, wireframe_id)
    return [
        WireframePageResponseDTO(
            page_id=p.page_id,
            wireframe_id=p.wireframe_id,
            project_id=p.project_id,
            entity_id=p.entity_id,
            entity_name=p.entity_name,
            page_name=p.page_name,
            page_type=p.page_type,
            confidence=p.confidence,
            mapping_source=p.mapping_source,
            svg_content=p.svg_content,
            layout_json=p.layout_json,
            status=p.status,
            sort_order=p.sort_order,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in pages
    ]


@router.get(
    "/wireframe-pages/{page_id}",
    response_model=WireframePageResponseDTO,
)
async def get_wireframe_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
) -> WireframePageResponseDTO:
    """Get a wireframe page by ID."""
    svc = WireframePageService(db)
    page = await svc.get_page(page_id)
    return WireframePageResponseDTO(
        page_id=page.page_id,
        wireframe_id=page.wireframe_id,
        project_id=page.project_id,
        entity_id=page.entity_id,
        entity_name=page.entity_name,
        page_name=page.page_name,
        page_type=page.page_type,
        confidence=page.confidence,
        mapping_source=page.mapping_source,
        svg_content=page.svg_content,
        layout_json=page.layout_json,
        status=page.status,
        sort_order=page.sort_order,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


@router.patch(
    "/wireframe-pages/{page_id}",
    response_model=WireframePageResponseDTO,
)
async def update_wireframe_page(
    page_id: str,
    dto: WireframePageUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> WireframePageResponseDTO:
    """Update a wireframe page."""
    svc = WireframePageService(db)
    page = await svc.update_page(page_id, dto.model_dump(exclude_unset=True))
    return WireframePageResponseDTO(
        page_id=page.page_id,
        wireframe_id=page.wireframe_id,
        project_id=page.project_id,
        entity_id=page.entity_id,
        entity_name=page.entity_name,
        page_name=page.page_name,
        page_type=page.page_type,
        confidence=page.confidence,
        mapping_source=page.mapping_source,
        svg_content=page.svg_content,
        layout_json=page.layout_json,
        status=page.status,
        sort_order=page.sort_order,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


@router.delete(
    "/wireframe-pages/{page_id}",
    status_code=204,
    response_model=None,
)
async def delete_wireframe_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a wireframe page."""
    svc = WireframePageService(db)
    await svc.delete_page(page_id)


# ------------------------------------------------------------------
# Wireframe nav link endpoints
# ------------------------------------------------------------------

@router.get(
    "/projects/{project_id}/wireframe-nav-links",
    response_model=list[WireframeNavLinkResponseDTO],
)
async def list_wireframe_nav_links(
    project_id: str,
    wireframe_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[WireframeNavLinkResponseDTO]:
    """List wireframe nav links for a project."""
    svc = WireframeNavLinkService(db)
    links = await svc.list_links(project_id, wireframe_id)
    return [
        WireframeNavLinkResponseDTO(
            link_id=link.link_id,
            wireframe_id=link.wireframe_id,
            project_id=link.project_id,
            source_page_id=link.source_page_id,
            target_page_id=link.target_page_id,
            interface_refs_json=link.interface_refs_json,
            relation_strength=link.relation_strength,
            interface_count=link.interface_count,
            is_marked_missing=link.is_marked_missing,
            created_at=link.created_at,
            updated_at=link.updated_at,
        )
        for link in links
    ]
