"""LLM provider API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.schemas.llm_provider import (
    LlmProviderCreate,
    LlmProviderListResponse,
    LlmProviderResponse,
    LlmProviderUpdate,
    ProviderTestResponse,
)
from app.services.llm_provider_service import LlmProviderService

router = APIRouter(prefix="/llm/providers", tags=["LLM Providers"])


def _current_user_id() -> str:
    """Placeholder authentication dependency."""
    return "user-mvp"


def _provider_to_response(provider: Any) -> LlmProviderResponse:
    """Convert ORM provider to response schema without secrets."""
    return LlmProviderResponse.model_validate(provider)


class ProviderQuery(BaseModel):
    """Query model for listing LLM providers."""

    scope: str | None = Query(None)
    scope_target: str | None = Query(None)
    keyword: str | None = Query(None)
    is_enabled: bool | None = Query(None)
    page: int = Query(1, ge=1)
    size: int = Query(100, ge=1, le=1000)


@router.get("", response_model=LlmProviderListResponse)
async def list_providers(
    q: ProviderQuery = Depends(),
    db: AsyncSession = Depends(get_db),
) -> LlmProviderListResponse:
    """List LLM providers with filters."""
    svc = LlmProviderService(db)
    offset = (q.page - 1) * q.size
    providers, total = await svc.list_providers(
        scope=q.scope,
        scope_target=q.scope_target,
        keyword=q.keyword,
        is_enabled=q.is_enabled,
        limit=q.size,
        offset=offset,
    )
    return LlmProviderListResponse(
        items=[_provider_to_response(p) for p in providers],
        total=total,
    )


@router.post("", response_model=LlmProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    dto: LlmProviderCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> LlmProviderResponse:
    """Create an LLM provider."""
    svc = LlmProviderService(db)
    provider = await svc.create_provider(dto, user_id=user_id)
    return _provider_to_response(provider)


@router.get("/{provider_id}", response_model=LlmProviderResponse)
async def get_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
) -> LlmProviderResponse:
    """Get an LLM provider by ID."""
    svc = LlmProviderService(db)
    provider = await svc.get_provider(provider_id)
    return _provider_to_response(provider)


@router.put("/{provider_id}", response_model=LlmProviderResponse)
async def update_provider(
    provider_id: str,
    dto: LlmProviderUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> LlmProviderResponse:
    """Update an LLM provider."""
    svc = LlmProviderService(db)
    provider = await svc.update_provider(provider_id, dto, user_id=user_id)
    return _provider_to_response(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an LLM provider."""
    svc = LlmProviderService(db)
    try:
        await svc.delete_provider(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{provider_id}/clone", response_model=LlmProviderResponse)
async def clone_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> LlmProviderResponse:
    """Clone an LLM provider."""
    svc = LlmProviderService(db)
    provider = await svc.clone_provider(provider_id, user_id=user_id)
    return _provider_to_response(provider)


@router.post("/{provider_id}/set-default", response_model=LlmProviderResponse)
async def set_default_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> LlmProviderResponse:
    """Set an LLM provider as default for its scope."""
    svc = LlmProviderService(db)
    provider = await svc.set_default(provider_id)
    return _provider_to_response(provider)


@router.post("/{provider_id}/test", response_model=ProviderTestResponse)
async def test_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProviderTestResponse:
    """Test connectivity of an LLM provider."""
    svc = LlmProviderService(db)
    result = await svc.test_provider(provider_id)
    return ProviderTestResponse(**result)
