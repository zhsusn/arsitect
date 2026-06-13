"""Application router — CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.database.session import get_db
from app.models.application import Application
from app.schemas.common import PageResponse
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationCreateDTO(BaseModel):
    """Request body for creating an application."""

    application_id: str = Field(..., max_length=36)
    application_name: str = Field(..., max_length=100)
    local_path: str = Field(..., max_length=4096)
    description: str | None = Field(default=None, max_length=500)
    workspace_id: str = Field(default="default", max_length=36)


class ApplicationUpdateDTO(BaseModel):
    """Request body for partially updating an application."""

    application_name: str | None = Field(default=None, max_length=100)
    local_path: str | None = Field(default=None, max_length=4096)
    description: str | None = Field(default=None, max_length=500)


class ApplicationResponseDTO(BaseModel):
    """Response model for application data."""

    model_config = {"from_attributes": True}

    application_id: str
    application_name: str
    description: str | None
    local_path: str
    workspace_id: str
    path_accessible: bool


@router.post(
    "",
    response_model=ApplicationResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_application(
    dto: ApplicationCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> Application:
    """Create a new application."""
    svc = ApplicationService(db)
    try:
        return await svc.create_application(
            application_id=dto.application_id,
            application_name=dto.application_name,
            local_path=dto.local_path,
            description=dto.description,
            workspace_id=dto.workspace_id,
        )
    except Exception as exc:
        if "UNIQUE constraint" in str(exc):
            raise ConflictError(
                detail=f"Application '{dto.application_name}' already exists"
            ) from exc
        raise


@router.get("", response_model=PageResponse[ApplicationResponseDTO])
async def list_applications(
    workspace_id: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
) -> PageResponse[ApplicationResponseDTO]:
    """List all applications with pagination."""
    svc = ApplicationService(db)
    items, total = await svc.list_applications(
        page=page, page_size=page_size, workspace_id=workspace_id
    )
    total_pages = (total + page_size - 1) // page_size
    return PageResponse[ApplicationResponseDTO](
        data=[ApplicationResponseDTO.model_validate(a) for a in items],
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.get("/{application_id}", response_model=ApplicationResponseDTO)
async def get_application(
    application_id: str,
    db: AsyncSession = Depends(get_db),
) -> Application:
    """Get a single application by ID."""
    svc = ApplicationService(db)
    app = await svc.get_application(application_id)
    if app is None:
        raise NotFoundError(detail=f"Application '{application_id}' not found")
    return app


@router.patch("/{application_id}", response_model=ApplicationResponseDTO)
async def update_application(
    application_id: str,
    dto: ApplicationUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> Application:
    """Partially update an existing application."""
    svc = ApplicationService(db)
    updated = await svc.update_application(
        application_id,
        application_name=dto.application_name,
        local_path=dto.local_path,
        description=dto.description,
    )
    if updated is None:
        raise NotFoundError(
            detail=f"Application '{application_id}' not found"
        )
    return updated


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_application(
    application_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an application."""
    svc = ApplicationService(db)
    result = await svc.delete_application(application_id)
    if not result:
        raise NotFoundError(
            detail=f"Application '{application_id}' not found"
        )
