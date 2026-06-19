"""LLM policy API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import get_db
from app.schemas.llm_policy import (
    ApplyTemplateRequest,
    LlmPolicyCreate,
    LlmPolicyListResponse,
    LlmPolicyResponse,
    LlmPolicyUpdate,
    PolicyCheckRequest,
    PolicyCheckResponse,
)
from app.schemas.llm_policy_rule import (
    LlmPolicyRuleCreate,
    LlmPolicyRuleResponse,
    UpdateRuleOrderRequest,
)
from app.schemas.policy_template import PolicyTemplateListResponse, PolicyTemplateResponse
from app.services.llm_policy_service import LlmPolicyService
from app.services.llm_rule_engine import LlmRuleEngine

router = APIRouter(prefix="/llm/policies", tags=["LLM Policies"])


def _current_user_id() -> str:
    """Placeholder authentication dependency."""
    return "user-mvp"


def _policy_to_response(policy: Any) -> LlmPolicyResponse:
    """Convert ORM policy to response schema."""
    return LlmPolicyResponse.model_validate(policy)


class PolicyQuery(BaseModel):
    """Query model for listing LLM policies."""

    scope: str | None = Query(None)
    scope_target: str | None = Query(None)
    keyword: str | None = Query(None)
    is_enabled: bool | None = Query(None)
    page: int = Query(1, ge=1)
    size: int = Query(100, ge=1, le=1000)


@router.get("", response_model=LlmPolicyListResponse)
async def list_policies(
    q: PolicyQuery = Depends(),
    db: AsyncSession = Depends(get_db),
) -> LlmPolicyListResponse:
    """List LLM policies with filters."""
    svc = LlmPolicyService(db)
    offset = (q.page - 1) * q.size
    policies, total = await svc.list_policies(
        scope=q.scope,
        scope_target=q.scope_target,
        keyword=q.keyword,
        is_enabled=q.is_enabled,
        limit=q.size,
        offset=offset,
    )
    return LlmPolicyListResponse(
        items=[_policy_to_response(p) for p in policies],
        total=total,
    )


@router.post("", response_model=LlmPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    dto: LlmPolicyCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> LlmPolicyResponse:
    """Create an LLM policy."""
    svc = LlmPolicyService(db)
    policy = await svc.create_policy(dto, user_id=user_id)
    return _policy_to_response(policy)


@router.get("/templates", response_model=PolicyTemplateListResponse)
async def list_templates(
    db: AsyncSession = Depends(get_db),
) -> PolicyTemplateListResponse:
    """List built-in policy templates."""
    svc = LlmPolicyService(db)
    templates = await svc.list_templates()
    return PolicyTemplateListResponse(
        items=[PolicyTemplateResponse.model_validate(t) for t in templates],
        total=len(templates),
    )


@router.post("/apply-template", response_model=LlmPolicyResponse)
async def apply_template(
    req: ApplyTemplateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> LlmPolicyResponse:
    """Apply a template to a policy.

    If ``base_policy_id`` is provided, it overrides the default.
    """
    svc = LlmPolicyService(db)
    base_policy_id = req.base_policy_id
    if base_policy_id is None:
        policy = await svc.get_policy_by_key("global", None, "default")
        if policy is None:
            raise NotFoundError("未找到可应用模板的默认策略")
        base_policy_id = policy.id
    updated = await svc.apply_template(base_policy_id, req.template_id)
    return _policy_to_response(updated)


@router.get("/{policy_id}", response_model=LlmPolicyResponse)
async def get_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
) -> LlmPolicyResponse:
    """Get an LLM policy by ID."""
    svc = LlmPolicyService(db)
    policy = await svc.get_policy(policy_id)
    return _policy_to_response(policy)


@router.put("/{policy_id}", response_model=LlmPolicyResponse)
async def update_policy(
    policy_id: str,
    dto: LlmPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> LlmPolicyResponse:
    """Update an LLM policy."""
    svc = LlmPolicyService(db)
    policy = await svc.update_policy(policy_id, dto, user_id=user_id)
    return _policy_to_response(policy)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an LLM policy."""
    svc = LlmPolicyService(db)
    await svc.delete_policy(policy_id)


@router.post("/{policy_id}/rules", response_model=LlmPolicyRuleResponse)
async def append_rule(
    policy_id: str,
    dto: LlmPolicyRuleCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> LlmPolicyRuleResponse:
    """Append a single rule to a policy."""
    svc = LlmPolicyService(db)
    rule = await svc.append_rule(policy_id, dto, user_id=user_id)
    return LlmPolicyRuleResponse.model_validate(rule)


@router.put("/{policy_id}/rules/order", response_model=list[LlmPolicyRuleResponse])
async def update_rule_order(
    policy_id: str,
    req: UpdateRuleOrderRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> list[LlmPolicyRuleResponse]:
    """Update sort order of rules within a policy."""
    svc = LlmPolicyService(db)
    rules = await svc.update_rule_order(policy_id, req.rule_ids)
    return [LlmPolicyRuleResponse.model_validate(r) for r in rules]


@router.post("/check", response_model=PolicyCheckResponse)
async def check_permission(
    req: PolicyCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> PolicyCheckResponse:
    """Check permission decision for a tool request."""
    policy_svc = LlmPolicyService(db)
    engine = LlmRuleEngine(policy_svc)
    if req.policy_id:
        result = await engine.check_by_policy_id(
            req.policy_id, req.action_type, req.target
        )
    else:
        result = await engine.check(
            db,
            policy_key=req.policy_key,
            scope=req.scope,
            scope_target=req.scope_target,
            action_type=req.action_type,
            target=req.target,
            project_id=req.project_id,
            user_id=req.user_id,
        )
    return PolicyCheckResponse(**result)
