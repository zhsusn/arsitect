"""Sketch router — CRUD + generation for sketches."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.schemas.sketch import (
    SketchCreateDTO,
    SketchGenerateDTO,
    SketchGenerateFromRequirementsDTO,
    SketchResponseDTO,
    SketchUpdateDTO,
)
from app.schemas.sketch_page import (
    SketchPageCreateDTO,
    SketchPageResponseDTO,
    SketchPageUpdateDTO,
)
from app.services.sketch_page_service import SketchPageService
from app.services.sketch_service import SketchService

router = APIRouter(tags=["sketches"])


# ------------------------------------------------------------------
# Sketch session endpoints
# ------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/sketches",
    response_model=SketchResponseDTO,
    status_code=201,
)
async def create_sketch(
    project_id: str,
    dto: SketchCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> SketchResponseDTO:
    """Create a new sketch session for a project."""
    svc = SketchService(db)
    sketch = await svc.create_sketch(
        project_id=project_id,
        name=dto.name,
        source_story_ids=dto.source_story_ids,
        status=dto.status,
    )
    return SketchResponseDTO(
        sketch_id=sketch.sketch_id,
        project_id=sketch.project_id,
        name=sketch.name,
        source_story_ids=sketch.source_story_ids,
        page_count=sketch.page_count,
        coverage_percent=sketch.coverage_percent,
        validation_report=sketch.validation_report,
        status=sketch.status,
        created_at=sketch.created_at,
        updated_at=sketch.updated_at,
    )


@router.post(
    "/projects/{project_id}/sketches/generate",
    response_model=SketchResponseDTO,
    status_code=201,
)
async def generate_sketch(
    project_id: str,
    dto: SketchGenerateDTO,
    db: AsyncSession = Depends(get_db),
) -> SketchResponseDTO:
    """Generate sketch pages from user stories."""
    svc = SketchService(db)
    sketch = await svc.generate_from_stories(
        project_id=project_id,
        story_ids=dto.story_ids,
    )
    return SketchResponseDTO(
        sketch_id=sketch.sketch_id,
        project_id=sketch.project_id,
        name=sketch.name,
        source_story_ids=sketch.source_story_ids,
        page_count=sketch.page_count,
        coverage_percent=sketch.coverage_percent,
        validation_report=sketch.validation_report,
        status=sketch.status,
        created_at=sketch.created_at,
        updated_at=sketch.updated_at,
    )


@router.post(
    "/projects/{project_id}/sketches/generate-from-requirements",
    response_model=SketchResponseDTO,
    status_code=201,
)
async def generate_sketch_from_requirements(
    project_id: str,
    dto: SketchGenerateFromRequirementsDTO,
    db: AsyncSession = Depends(get_db),
) -> SketchResponseDTO:
    """Generate sketch pages from detailed requirement documents."""
    svc = SketchService(db)
    sketch = await svc.generate_from_requirements(
        project_id=project_id,
        story_ids=dto.story_ids,
    )
    return SketchResponseDTO(
        sketch_id=sketch.sketch_id,
        project_id=sketch.project_id,
        name=sketch.name,
        source_story_ids=sketch.source_story_ids,
        page_count=sketch.page_count,
        coverage_percent=sketch.coverage_percent,
        validation_report=sketch.validation_report,
        status=sketch.status,
        created_at=sketch.created_at,
        updated_at=sketch.updated_at,
    )


@router.get(
    "/projects/{project_id}/sketches",
    response_model=list[SketchResponseDTO],
)
async def list_sketches(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[SketchResponseDTO]:
    """List sketches for a project."""
    svc = SketchService(db)
    sketches = await svc.list_sketches(project_id)
    return [
        SketchResponseDTO(
            sketch_id=s.sketch_id,
            project_id=s.project_id,
            name=s.name,
            source_story_ids=s.source_story_ids,
            page_count=s.page_count,
            coverage_percent=s.coverage_percent,
            validation_report=s.validation_report,
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sketches
    ]


@router.get(
    "/sketches/{sketch_id}",
    response_model=SketchResponseDTO,
)
async def get_sketch(
    sketch_id: str,
    db: AsyncSession = Depends(get_db),
) -> SketchResponseDTO:
    """Get a single sketch session by ID."""
    svc = SketchService(db)
    sketch = await svc.get_sketch(sketch_id)
    return SketchResponseDTO(
        sketch_id=sketch.sketch_id,
        project_id=sketch.project_id,
        name=sketch.name,
        source_story_ids=sketch.source_story_ids,
        page_count=sketch.page_count,
        coverage_percent=sketch.coverage_percent,
        validation_report=sketch.validation_report,
        status=sketch.status,
        created_at=sketch.created_at,
        updated_at=sketch.updated_at,
    )


@router.patch(
    "/sketches/{sketch_id}",
    response_model=SketchResponseDTO,
)
async def update_sketch(
    sketch_id: str,
    dto: SketchUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> SketchResponseDTO:
    """Update a sketch session."""
    svc = SketchService(db)
    sketch = await svc.update_sketch(
        sketch_id,
        dto.model_dump(exclude_unset=True),
    )
    return SketchResponseDTO(
        sketch_id=sketch.sketch_id,
        project_id=sketch.project_id,
        name=sketch.name,
        source_story_ids=sketch.source_story_ids,
        page_count=sketch.page_count,
        coverage_percent=sketch.coverage_percent,
        validation_report=sketch.validation_report,
        status=sketch.status,
        created_at=sketch.created_at,
        updated_at=sketch.updated_at,
    )


@router.delete(
    "/sketches/{sketch_id}",
    status_code=204,
    response_model=None,
)
async def delete_sketch(
    sketch_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a sketch session."""
    svc = SketchService(db)
    await svc.delete_sketch(sketch_id)


# ------------------------------------------------------------------
# Sketch page endpoints
# ------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/sketch-pages",
    response_model=SketchPageResponseDTO,
    status_code=201,
)
async def create_sketch_page(
    project_id: str,
    dto: SketchPageCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> SketchPageResponseDTO:
    """Create a new sketch page."""
    svc = SketchPageService(db)
    page = await svc.create_page(
        project_id=project_id,
        story_id=dto.story_id,
        page_name=dto.page_name,
        page_type=dto.page_type,
        svg_content=dto.svg_content,
        fields_json=dto.fields_json,
        buttons_json=dto.buttons_json,
        nav_targets_json=dto.nav_targets_json,
        status=dto.status,
        sort_order=dto.sort_order,
        source_module_id=dto.source_module_id,
        source_md_path=dto.source_md_path,
    )
    return SketchPageResponseDTO(
        page_id=page.page_id,
        project_id=page.project_id,
        story_id=page.story_id,
        page_name=page.page_name,
        page_type=page.page_type,
        svg_content=page.svg_content,
        fields_json=page.fields_json,
        buttons_json=page.buttons_json,
        nav_targets_json=page.nav_targets_json,
        source_module_id=page.source_module_id,
        source_md_path=page.source_md_path,
        status=page.status,
        sort_order=page.sort_order,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


@router.get(
    "/projects/{project_id}/sketch-pages",
    response_model=list[SketchPageResponseDTO],
)
async def list_sketch_pages(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[SketchPageResponseDTO]:
    """List sketch pages for a project."""
    svc = SketchPageService(db)
    pages = await svc.list_pages(project_id)
    return [
        SketchPageResponseDTO(
            page_id=p.page_id,
            project_id=p.project_id,
            story_id=p.story_id,
            page_name=p.page_name,
            page_type=p.page_type,
            svg_content=p.svg_content,
            fields_json=p.fields_json,
            buttons_json=p.buttons_json,
            nav_targets_json=p.nav_targets_json,
            source_module_id=p.source_module_id,
            source_md_path=p.source_md_path,
            status=p.status,
            sort_order=p.sort_order,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in pages
    ]


@router.get(
    "/sketch-pages/{page_id}",
    response_model=SketchPageResponseDTO,
)
async def get_sketch_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
) -> SketchPageResponseDTO:
    """Get a single sketch page by ID."""
    svc = SketchPageService(db)
    page = await svc.get_page(page_id)
    return SketchPageResponseDTO(
        page_id=page.page_id,
        project_id=page.project_id,
        story_id=page.story_id,
        page_name=page.page_name,
        page_type=page.page_type,
        svg_content=page.svg_content,
        fields_json=page.fields_json,
        buttons_json=page.buttons_json,
        nav_targets_json=page.nav_targets_json,
        source_module_id=page.source_module_id,
        source_md_path=page.source_md_path,
        status=page.status,
        sort_order=page.sort_order,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


@router.patch(
    "/sketch-pages/{page_id}",
    response_model=SketchPageResponseDTO,
)
async def update_sketch_page(
    page_id: str,
    dto: SketchPageUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> SketchPageResponseDTO:
    """Update a sketch page."""
    svc = SketchPageService(db)
    page = await svc.update_page(page_id, dto.model_dump(exclude_unset=True))
    return SketchPageResponseDTO(
        page_id=page.page_id,
        project_id=page.project_id,
        story_id=page.story_id,
        page_name=page.page_name,
        page_type=page.page_type,
        svg_content=page.svg_content,
        fields_json=page.fields_json,
        buttons_json=page.buttons_json,
        nav_targets_json=page.nav_targets_json,
        source_module_id=page.source_module_id,
        source_md_path=page.source_md_path,
        status=page.status,
        sort_order=page.sort_order,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


@router.delete(
    "/sketch-pages/{page_id}",
    status_code=204,
    response_model=None,
)
async def delete_sketch_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a sketch page."""
    svc = SketchPageService(db)
    await svc.delete_page(page_id)
