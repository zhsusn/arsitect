"""OpenUI router — CRUD + generation for OpenUI specs."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.schemas.open_ui import (
    OpenUICreateDTO,
    OpenUIGenerateDTO,
    OpenUIHealthResponseDTO,
    OpenUIResponseDTO,
    OpenUIUpdateDTO,
)
from app.schemas.open_ui_page import (
    OpenUIPageCreateDTO,
    OpenUIPageResponseDTO,
    OpenUIPageUpdateDTO,
)
from app.services.open_ui_page_service import OpenUIPageService
from app.services.open_ui_service import OpenUIService

router = APIRouter(tags=["open-ui"])


# ------------------------------------------------------------------
# OpenUI spec endpoints
# ------------------------------------------------------------------


@router.post(
    "/projects/{project_id}/open-ui-specs",
    response_model=OpenUIResponseDTO,
    status_code=201,
)
async def create_spec(
    project_id: str,
    dto: OpenUICreateDTO,
    db: AsyncSession = Depends(get_db),
) -> OpenUIResponseDTO:
    """Create a new OpenUI spec session."""
    svc = OpenUIService(db)
    spec = await svc.create_spec(
        project_id=project_id,
        spec_name=dto.spec_name,
        status=dto.status,
    )
    return OpenUIResponseDTO(
        spec_id=spec.spec_id,
        project_id=spec.project_id,
        spec_name=spec.spec_name,
        prompt_text=spec.prompt_text,
        page_count=spec.page_count,
        page_titles_json=spec.page_titles_json,
        service_status=spec.service_status,
        generation_duration_ms=spec.generation_duration_ms,
        content_hash=spec.content_hash,
        status=spec.status,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
    )


@router.post(
    "/projects/{project_id}/open-ui-specs/generate",
    response_model=OpenUIResponseDTO,
    status_code=201,
)
async def generate_spec(
    project_id: str,
    dto: OpenUIGenerateDTO,
    db: AsyncSession = Depends(get_db),
) -> OpenUIResponseDTO:
    """Generate OpenUI prototype from C4 + interface contracts."""
    svc = OpenUIService(db)
    spec = await svc.generate_from_c4(project_id=project_id)
    return OpenUIResponseDTO(
        spec_id=spec.spec_id,
        project_id=spec.project_id,
        spec_name=spec.spec_name,
        prompt_text=spec.prompt_text,
        page_count=spec.page_count,
        page_titles_json=spec.page_titles_json,
        service_status=spec.service_status,
        generation_duration_ms=spec.generation_duration_ms,
        content_hash=spec.content_hash,
        status=spec.status,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
    )


@router.get(
    "/projects/{project_id}/open-ui-specs",
    response_model=list[OpenUIResponseDTO],
)
async def list_specs(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[OpenUIResponseDTO]:
    """List OpenUI specs for a project."""
    svc = OpenUIService(db)
    specs = await svc.list_specs(project_id)
    return [
        OpenUIResponseDTO(
            spec_id=s.spec_id,
            project_id=s.project_id,
            spec_name=s.spec_name,
            prompt_text=s.prompt_text,
            page_count=s.page_count,
            page_titles_json=s.page_titles_json,
            service_status=s.service_status,
            generation_duration_ms=s.generation_duration_ms,
            content_hash=s.content_hash,
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in specs
    ]


@router.get(
    "/open-ui-specs/{spec_id}",
    response_model=OpenUIResponseDTO,
)
async def get_spec(
    spec_id: str,
    db: AsyncSession = Depends(get_db),
) -> OpenUIResponseDTO:
    """Get an OpenUI spec by ID."""
    svc = OpenUIService(db)
    spec = await svc.get_spec(spec_id)
    return OpenUIResponseDTO(
        spec_id=spec.spec_id,
        project_id=spec.project_id,
        spec_name=spec.spec_name,
        prompt_text=spec.prompt_text,
        page_count=spec.page_count,
        page_titles_json=spec.page_titles_json,
        service_status=spec.service_status,
        generation_duration_ms=spec.generation_duration_ms,
        content_hash=spec.content_hash,
        status=spec.status,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
    )


@router.get(
    "/open-ui-specs/{spec_id}/health",
    response_model=OpenUIHealthResponseDTO,
)
async def check_spec_health(
    spec_id: str,
    db: AsyncSession = Depends(get_db),
) -> OpenUIHealthResponseDTO:
    """Check OpenUI service health for a spec."""
    svc = OpenUIService(db)
    result = await svc.check_health(spec_id)
    return OpenUIHealthResponseDTO(**result)


@router.patch(
    "/open-ui-specs/{spec_id}",
    response_model=OpenUIResponseDTO,
)
async def update_spec(
    spec_id: str,
    dto: OpenUIUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> OpenUIResponseDTO:
    """Update an OpenUI spec."""
    svc = OpenUIService(db)
    spec = await svc.update_spec(spec_id, dto.model_dump(exclude_unset=True))
    return OpenUIResponseDTO(
        spec_id=spec.spec_id,
        project_id=spec.project_id,
        spec_name=spec.spec_name,
        prompt_text=spec.prompt_text,
        page_count=spec.page_count,
        page_titles_json=spec.page_titles_json,
        service_status=spec.service_status,
        generation_duration_ms=spec.generation_duration_ms,
        content_hash=spec.content_hash,
        status=spec.status,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
    )


@router.delete(
    "/open-ui-specs/{spec_id}",
    status_code=204,
    response_model=None,
)
async def delete_spec(
    spec_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an OpenUI spec."""
    svc = OpenUIService(db)
    await svc.delete_spec(spec_id)


# ------------------------------------------------------------------
# OpenUI page endpoints
# ------------------------------------------------------------------


@router.post(
    "/projects/{project_id}/open-ui-pages",
    response_model=OpenUIPageResponseDTO,
    status_code=201,
)
async def create_open_ui_page(
    project_id: str,
    dto: OpenUIPageCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> OpenUIPageResponseDTO:
    """Create an OpenUI page."""
    svc = OpenUIPageService(db)
    page = await svc.create_page(
        spec_id=dto.spec_id,
        project_id=project_id,
        container_id=dto.container_id,
        page_title=dto.page_title,
        html_content=dto.html_content,
        page_index=dto.page_index,
        status=dto.status,
    )
    return OpenUIPageResponseDTO(
        page_id=page.page_id,
        spec_id=page.spec_id,
        project_id=page.project_id,
        container_id=page.container_id,
        page_title=page.page_title,
        html_content=page.html_content,
        page_index=page.page_index,
        status=page.status,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


@router.get(
    "/projects/{project_id}/open-ui-pages",
    response_model=list[OpenUIPageResponseDTO],
)
async def list_open_ui_pages(
    project_id: str,
    spec_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[OpenUIPageResponseDTO]:
    """List OpenUI pages for a project."""
    svc = OpenUIPageService(db)
    pages = await svc.list_pages(project_id, spec_id)
    return [
        OpenUIPageResponseDTO(
            page_id=p.page_id,
            spec_id=p.spec_id,
            project_id=p.project_id,
            container_id=p.container_id,
            page_title=p.page_title,
            html_content=p.html_content,
            page_index=p.page_index,
            status=p.status,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in pages
    ]


@router.get(
    "/open-ui-pages/{page_id}",
    response_model=OpenUIPageResponseDTO,
)
async def get_open_ui_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
) -> OpenUIPageResponseDTO:
    """Get an OpenUI page by ID."""
    svc = OpenUIPageService(db)
    page = await svc.get_page(page_id)
    return OpenUIPageResponseDTO(
        page_id=page.page_id,
        spec_id=page.spec_id,
        project_id=page.project_id,
        container_id=page.container_id,
        page_title=page.page_title,
        html_content=page.html_content,
        page_index=page.page_index,
        status=page.status,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


@router.patch(
    "/open-ui-pages/{page_id}",
    response_model=OpenUIPageResponseDTO,
)
async def update_open_ui_page(
    page_id: str,
    dto: OpenUIPageUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> OpenUIPageResponseDTO:
    """Update an OpenUI page."""
    svc = OpenUIPageService(db)
    page = await svc.update_page(page_id, dto.model_dump(exclude_unset=True))
    return OpenUIPageResponseDTO(
        page_id=page.page_id,
        spec_id=page.spec_id,
        project_id=page.project_id,
        container_id=page.container_id,
        page_title=page.page_title,
        html_content=page.html_content,
        page_index=page.page_index,
        status=page.status,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


@router.delete(
    "/open-ui-pages/{page_id}",
    status_code=204,
    response_model=None,
)
async def delete_open_ui_page(
    page_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an OpenUI page."""
    svc = OpenUIPageService(db)
    await svc.delete_page(page_id)
