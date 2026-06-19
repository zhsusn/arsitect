"""Seed default LLM configuration on application startup."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.governance.template_engine import TemplateEngine
from app.models.llm_provider import LlmProvider
from app.models.policy_template import PolicyTemplate
from app.models.template import Template
from app.models.template_stage import TemplateStage
from app.schemas.llm_policy import LlmPolicyCreate
from app.schemas.llm_provider import LlmProviderCreate
from app.services.llm_policy_service import LlmPolicyService
from app.services.llm_provider_service import LlmProviderService


def _policy_templates() -> list[dict[str, Any]]:
    """Return built-in policy template seed data."""
    return [
        {
            "id": "personal",
            "name": "个人开发模式",
            "description": "宽松策略，减少 AI 打断，适合本地开发",
            "default_mode": "ask",
            "rules_json": [
                {
                    "category": "file_system",
                    "action_type": "file_read",
                    "permission": "allow",
                    "pattern": "${PROJECT_ROOT}/**",
                    "description": "允许读取项目内文件",
                },
                {
                    "category": "file_system",
                    "action_type": "file_write",
                    "permission": "allow",
                    "pattern": "{src/**,tests/**,config/**}",
                    "description": "允许写入常见开发目录",
                },
                {
                    "category": "file_system",
                    "action_type": "file_write",
                    "permission": "ask",
                    "pattern": "${PROJECT_ROOT}/**",
                    "description": "其他写入需确认",
                },
                {
                    "category": "file_system",
                    "action_type": "file_delete",
                    "permission": "ask",
                    "pattern": "*",
                    "description": "删除文件需确认",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "pytest*",
                    "description": "允许单元测试",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "python -m pytest*",
                    "description": "允许单元测试",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "ruff check*",
                    "description": "允许代码检查",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "ruff format*",
                    "description": "允许代码格式化",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "npm test",
                    "description": "允许运行测试",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "npm run build",
                    "description": "允许构建",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "npm run lint",
                    "description": "允许 lint",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "npm install*",
                    "description": "允许安装依赖",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "git status*",
                    "description": "允许 Git 状态查看",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "git diff*",
                    "description": "允许 Git diff",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "git log*",
                    "description": "允许 Git log",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "ask",
                    "pattern": "*",
                    "description": "其他命令需确认",
                },
                {
                    "category": "network",
                    "action_type": "web_fetch",
                    "permission": "allow",
                    "pattern": "*",
                    "description": "允许抓取外部网页",
                },
                {
                    "category": "network",
                    "action_type": "external_api",
                    "permission": "ask",
                    "pattern": "*",
                    "description": "外部 API 调用需确认",
                },
                {
                    "category": "high_risk",
                    "action_type": "terminal",
                    "permission": "deny",
                    "pattern": "rm -rf*",
                    "description": "禁止递归删除",
                },
                {
                    "category": "high_risk",
                    "action_type": "terminal",
                    "permission": "deny",
                    "pattern": "sudo*",
                    "description": "禁止提权命令",
                },
            ],
        },
        {
            "id": "team",
            "name": "团队协作模式",
            "description": "平衡策略，适合团队协作",
            "default_mode": "ask",
            "rules_json": [
                {
                    "category": "file_system",
                    "action_type": "file_read",
                    "permission": "allow",
                    "pattern": "${PROJECT_ROOT}/**",
                    "description": "允许读取项目内文件",
                },
                {
                    "category": "file_system",
                    "action_type": "file_write",
                    "permission": "allow",
                    "pattern": "{src/**,tests/**}",
                    "description": "允许写入代码目录",
                },
                {
                    "category": "file_system",
                    "action_type": "file_write",
                    "permission": "ask",
                    "pattern": "{config/**,docs/**}",
                    "description": "配置与文档写入需确认",
                },
                {
                    "category": "file_system",
                    "action_type": "file_write",
                    "permission": "deny",
                    "pattern": "${PROJECT_ROOT}/**",
                    "description": "其他写入拒绝",
                },
                {
                    "category": "file_system",
                    "action_type": "file_delete",
                    "permission": "deny",
                    "pattern": "*",
                    "description": "禁止删除文件",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "{pytest*,npm test,ruff check*}",
                    "description": "允许测试与检查",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "allow",
                    "pattern": "{git status*,git diff*,git log*}",
                    "description": "允许 Git 只读",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "ask",
                    "pattern": "npm install*",
                    "description": "安装依赖需确认",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "deny",
                    "pattern": "{git commit*,git push*}",
                    "description": "禁止自动提交代码",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "ask",
                    "pattern": "*",
                    "description": "其他命令需确认",
                },
                {
                    "category": "network",
                    "action_type": "web_fetch",
                    "permission": "ask",
                    "pattern": "*",
                    "description": "外部网页抓取需确认",
                },
                {
                    "category": "network",
                    "action_type": "external_api",
                    "permission": "deny",
                    "pattern": "*",
                    "description": "禁止外部 API 调用",
                },
                {
                    "category": "high_risk",
                    "action_type": "terminal",
                    "permission": "deny",
                    "pattern": "{rm -rf *,sudo *,curl *|*bash*}",
                    "description": "高危命令拒绝",
                },
            ],
        },
        {
            "id": "enterprise",
            "name": "企业安全模式",
            "description": "默认拒绝，逐步放开",
            "default_mode": "deny",
            "rules_json": [
                {
                    "category": "file_system",
                    "action_type": "file_read",
                    "permission": "allow",
                    "pattern": "${PROJECT_ROOT}/**",
                    "description": "允许读取项目内文件",
                },
                {
                    "category": "file_system",
                    "action_type": "file_write",
                    "permission": "allow",
                    "pattern": "${PROJECT_ROOT}/openspec/changes/**",
                    "description": "仅允许写入指定目录",
                },
                {
                    "category": "file_system",
                    "action_type": "file_write",
                    "permission": "deny",
                    "pattern": "${PROJECT_ROOT}/**",
                    "description": "其他写入拒绝",
                },
                {
                    "category": "file_system",
                    "action_type": "file_delete",
                    "permission": "deny",
                    "pattern": "*",
                    "description": "禁止删除文件",
                },
                {
                    "category": "terminal",
                    "action_type": "terminal",
                    "permission": "deny",
                    "pattern": "*",
                    "description": "默认拒绝所有命令",
                },
                {
                    "category": "network",
                    "action_type": "web_fetch",
                    "permission": "deny",
                    "pattern": "*",
                    "description": "禁止外部网页抓取",
                },
                {
                    "category": "network",
                    "action_type": "external_api",
                    "permission": "deny",
                    "pattern": "*",
                    "description": "禁止外部 API 调用",
                },
                {
                    "category": "network",
                    "action_type": "external_api",
                    "permission": "allow",
                    "pattern": "https://internal-api.company.com/**",
                    "description": "允许内网白名单",
                },
                {
                    "category": "high_risk",
                    "action_type": "terminal",
                    "permission": "deny",
                    "pattern": "{rm -rf *,sudo *,curl *,wget *}",
                    "description": "高危命令拒绝",
                },
            ],
        },
    ]


async def _seed_policy_templates(session: AsyncSession) -> None:
    """Ensure built-in policy templates exist."""
    existing_result = await session.execute(
        select(PolicyTemplate.id).where(PolicyTemplate.id.in_(["personal", "team", "enterprise"]))
    )
    existing = {row[0] for row in existing_result.all()}
    for template in _policy_templates():
        if template["id"] in existing:
            continue
        session.add(
            PolicyTemplate(
                id=template["id"],
                name=template["name"],
                description=template["description"],
                default_mode=template["default_mode"],
                rules_json=template["rules_json"],
            )
        )
        print(f"[SEED] Created policy template: {template['name']}")
    await session.flush()


async def _seed_templates_and_stages(session: AsyncSession) -> None:
    """Seed default project templates and their stages from TemplateEngine."""
    engine = TemplateEngine()
    for route in engine.list_routes():
        tpl = engine.get_template(route)
        if tpl is None:
            continue
        template_id = route.capitalize()
        merge_policy = json.dumps(tpl.get_merge_policy())
        existing = await session.get(Template, template_id)
        if existing is None:
            session.add(
                Template(
                    template_id=template_id,
                    template_name=f"{template_id} 模板",
                    description=tpl.description,
                    stage_count=len(tpl.stages),
                    estimated_skill_count=sum(
                        1 + len(s.auxiliary_skill_ids) for s in tpl.stages
                    ),
                    applicable_complexity=template_id,
                    config_json=None,
                    default_execution_strategy=tpl.execution_strategy,
                    merge_policy_json=merge_policy,
                )
            )
            print(f"[SEED] Created project template: {template_id}")
        else:
            existing.default_execution_strategy = tpl.execution_strategy
            existing.merge_policy_json = merge_policy
            existing.stage_count = len(tpl.stages)
            existing.estimated_skill_count = sum(
                1 + len(s.auxiliary_skill_ids) for s in tpl.stages
            )
            session.add(existing)

        existing_stages_result = await session.execute(
            select(TemplateStage.business_stage_key).where(
                TemplateStage.template_id == template_id
            )
        )
        existing_stage_keys = {row[0] for row in existing_stages_result.all()}

        for stage in tpl.stages:
            if stage.business_stage_key in existing_stage_keys:
                continue
            session.add(
                TemplateStage(
                    stage_id=str(uuid.uuid4()),
                    stage_name=stage.stage_name,
                    business_stage_key=stage.business_stage_key,
                    order_index=stage.order,
                    template_id=template_id,
                    primary_skill_id=stage.primary_skill_id,
                    auxiliary_skill_ids=(
                        json.dumps(stage.auxiliary_skill_ids)
                        if stage.auxiliary_skill_ids
                        else None
                    ),
                    gate_id=None,
                    skippable=False,
                    merge_group_id=None,
                    is_present_in=template_id,
                    is_gate_required=stage.is_gate_required,
                    auto_advance=stage.auto_advance,
                )
            )
            print(f"[SEED] Created template stage: {template_id}/{stage.business_stage_key}")
    await session.flush()


async def _seed_default_provider(session: AsyncSession) -> None:
    """Seed a default global LLM provider from environment variables."""
    result = await session.execute(
        select(LlmProvider.id).where(LlmProvider.scope == "global").limit(1)
    )
    if result.scalar_one_or_none():
        return

    provider_env = settings.GOVERNANCE_LLM_PROVIDER.lower()
    if provider_env in {"kimi", "kimi-cli"}:
        provider_type = "kimi-cli"
        config_json: dict[str, Any] = {
            "kimi_cli_path": settings.KIMI_CLI_PATH,
            "timeout": 120,
        }
        name = "默认 Kimi CLI"
    elif provider_env in {"openai", "kimi-api"}:
        provider_type = "openai" if provider_env == "openai" else "kimi-api"
        config_json = {
            "api_base": settings.OPENAI_API_BASE or "https://api.openai.com/v1",
            "model": settings.OPENAI_MODEL,
        }
        name = "默认 OpenAI"
    else:
        provider_type = "arsitect-agent"
        config_json = {}
        name = f"默认 {provider_env}"

    svc = LlmProviderService(session)
    await svc.create_provider(
        LlmProviderCreate(
            scope="global",
            scope_target=None,
            key="default",
            name=name,
            description="启动时从环境变量预制的默认 LLM Provider",
            provider_type=provider_type,  # type: ignore[arg-type]
            config_json=config_json,
            api_key=settings.OPENAI_API_KEY if provider_type in {"openai", "kimi-api"} else None,
            is_enabled=True,
            is_default=True,
            priority=0,
        ),
        user_id="system",
    )
    print(f"[SEED] Created default LLM provider: {name}")


async def _seed_default_policy(session: AsyncSession) -> None:
    """Seed a default global LLM policy based on the personal template."""
    policy_svc = LlmPolicyService(session)
    existing = await policy_svc.get_policy_by_key("global", None, "default")
    if existing:
        return

    template_result = await session.execute(
        select(PolicyTemplate).where(PolicyTemplate.id == "personal")
    )
    template = template_result.scalar_one_or_none()
    if template is None:
        print("[SEED] Skipping default policy: personal template not found")
        return

    await policy_svc.create_policy(
        LlmPolicyCreate(
            scope="global",
            scope_target=None,
            key="default",
            name="默认 LLM 权限策略",
            description="启动时预制的安全默认权限策略，基于个人开发模板",
            default_mode=template.default_mode,  # type: ignore[arg-type]
            template_id=template.id,
            is_customized=False,
            is_enabled=True,
            priority=0,
            rules=template.rules_json,
        ),
        user_id="system",
    )
    print("[SEED] Created default LLM policy")


async def seed_default_config_nodes(session: AsyncSession) -> None:
    """Seed default LLM providers, policies and templates if none exist.

    Reads current environment variables to create an initial provider and a
    safe default permission policy. These become the source of truth for the
    LLM Config Center.
    """
    await _seed_templates_and_stages(session)
    await _seed_policy_templates(session)
    await _seed_default_provider(session)
    await _seed_default_policy(session)
