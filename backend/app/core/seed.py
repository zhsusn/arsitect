"""Seed default configuration nodes on application startup."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.config_node import ConfigNode
from app.schemas.config_node import ConfigNodeCreate
from app.services.config_service import ConfigService
from app.services.llm_permission_service import LLMPermissionService


async def seed_default_config_nodes(session: AsyncSession) -> None:
    """Seed default LLM provider and permission nodes if none exist.

    Reads current environment variables to create an initial Kimi CLI provider
    node and a safe default permission policy node. These nodes become the
    source of truth; users can override them dynamically via the LLM Config
    Center UI.
    """
    svc = ConfigService(session)

    # Seed default LLM provider from env vars.
    provider_exists = await session.execute(
        select(ConfigNode).where(
            ConfigNode.node_type == "llm_provider",
            ConfigNode.scope == "global",
            ConfigNode.is_enabled == True,  # noqa: E712
        )
    )
    if not provider_exists.scalar_one_or_none():
        provider = settings.GOVERNANCE_LLM_PROVIDER.lower()
        config_json: dict[str, object] = {"provider": provider}
        secret_json: dict[str, object] | None = None
        name = "默认 Kimi CLI"

        if provider in {"kimi", "kimi-cli"}:
            config_json["kimi_cli_path"] = settings.KIMI_CLI_PATH
            config_json["timeout"] = 120
            name = f"默认 Kimi CLI ({settings.KIMI_CLI_PATH})"
        elif provider == "openai":
            config_json["api_base"] = settings.OPENAI_API_BASE or "https://api.openai.com/v1"
            config_json["model"] = settings.OPENAI_MODEL
            secret_json = {"api_key": settings.OPENAI_API_KEY} if settings.OPENAI_API_KEY else None
            name = f"默认 OpenAI ({settings.OPENAI_MODEL})"

        await svc.create_node(
            ConfigNodeCreate(
                node_type="llm_provider",
                scope="global",
                key="default",
                name=name,
                description="启动时从环境变量预制的默认 LLM Provider 节点",
                is_default=True,
                priority=0,
                config_json=config_json,
                secret_json=secret_json,
            ),
            user_id="system",
        )
        print(f"[SEED] Created default llm_provider node: {name}")

    # Seed default permission policy if none exists.
    permission_exists = await session.execute(
        select(ConfigNode).where(
            ConfigNode.node_type == "llm_permission",
            ConfigNode.scope == "global",
            ConfigNode.is_enabled == True,  # noqa: E712
        )
    )
    if not permission_exists.scalar_one_or_none():
        perm_svc = LLMPermissionService(svc)
        policy = perm_svc.get_default_policy()
        await svc.create_node(
            ConfigNodeCreate(
                node_type="llm_permission",
                scope="global",
                key="default",
                name="默认 LLM 权限策略",
                description="启动时预制的安全默认权限策略，可在 LLM 配置中心修改",
                is_default=False,
                priority=0,
                config_json=policy,
            ),
            user_id="system",
        )
        print("[SEED] Created default llm_permission node")
