"""Unit tests for ConfigService and LLMPermissionService."""

from __future__ import annotations

from typing import Any

import pytest

from app.schemas.config_node import ConfigNodeCreate, ConfigNodeUpdate
from app.services.config_service import ConfigService
from app.services.llm_permission_service import (
    LLMPermissionService,
    PermissionCheckContext,
)


class TestConfigService:
    """Config node CRUD and resolution tests."""

    async def test_create_and_get_node(self, db_session: Any) -> None:
        """TEST-1701: create and retrieve a config node."""
        svc = ConfigService(db_session)
        dto = ConfigNodeCreate(
            node_type="llm_provider",
            scope="global",
            key="kimi-default",
            name="Kimi CLI 默认节点",
            config_json={"provider": "kimi-cli", "model": "kimi"},
        )
        node = await svc.create_node(dto, user_id="user-1")
        assert node.id
        assert node.key == "kimi-default"

        fetched = await svc.get_node(node.id)
        assert fetched.name == "Kimi CLI 默认节点"

    async def test_duplicate_key_raises(self, db_session: Any) -> None:
        """TEST-1702: duplicate composite key is rejected."""
        svc = ConfigService(db_session)
        dto = ConfigNodeCreate(
            node_type="llm_provider",
            scope="global",
            key="dup",
            name="Dup",
            config_json={},
        )
        await svc.create_node(dto)
        with pytest.raises(ValueError):
            await svc.create_node(dto)

    async def test_resolve_merges_scopes(self, db_session: Any) -> None:
        """TEST-1703: project config overrides global config."""
        svc = ConfigService(db_session)
        await svc.create_node(
            ConfigNodeCreate(
                node_type="llm_permission",
                scope="global",
                key="global-policy",
                name="全局策略",
                config_json={"default_mode": "ask", "rules": []},
            )
        )
        await svc.create_node(
            ConfigNodeCreate(
                node_type="llm_permission",
                scope="project",
                scope_target="proj-1",
                key="project-policy",
                name="项目策略",
                priority=10,
                config_json={"default_mode": "allow"},
            )
        )

        resolved = await svc.resolve("llm_permission", project_id="proj-1", user_id="user-1")
        assert resolved["config"]["default_mode"] == "allow"

    async def test_update_node(self, db_session: Any) -> None:
        """TEST-1704: update node fields."""
        svc = ConfigService(db_session)
        node = await svc.create_node(
            ConfigNodeCreate(
                node_type="llm_provider",
                scope="global",
                key="to-update",
                name="Old",
                config_json={},
            )
        )
        updated = await svc.update_node(
            node.id, ConfigNodeUpdate(name="New", is_enabled=False), user_id="u"
        )
        assert updated.name == "New"
        assert updated.is_enabled is False


class TestLLMPermissionService:
    """LLM permission evaluation tests."""

    async def test_default_mode_ask(self, db_session: Any) -> None:
        """TEST-1710: no rules defaults to ask."""
        svc = LLMPermissionService(ConfigService(db_session))
        ctx = PermissionCheckContext(category="file_write", path="backend/app/main.py")
        result = await svc.check(ctx)
        assert result["decision"] == "ask"

    async def test_allow_rule_overrides_default(self, db_session: Any) -> None:
        """TEST-1711: allow rule permits project file write."""
        config_svc = ConfigService(db_session)
        await config_svc.create_node(
            ConfigNodeCreate(
                node_type="llm_permission",
                scope="global",
                key="allow-write",
                name="允许写入",
                config_json={
                    "default_mode": "ask",
                    "rules": [
                        {
                            "category": "file_write",
                            "decision": "allow",
                            "path": "backend/app/main.py",
                        }
                    ],
                },
            )
        )
        svc = LLMPermissionService(config_svc)
        ctx = PermissionCheckContext(category="file_write", path="backend/app/main.py")
        result = await svc.check(ctx)
        assert result["decision"] == "allow"

    async def test_deny_rule_wins_over_allow(self, db_session: Any) -> None:
        """TEST-1712: deny rule always beats allow rule."""
        config_svc = ConfigService(db_session)
        await config_svc.create_node(
            ConfigNodeCreate(
                node_type="llm_permission",
                scope="global",
                key="allow-all",
                name="全部允许",
                priority=0,
                config_json={
                    "default_mode": "allow",
                    "rules": [
                        {
                            "category": "file_write",
                            "decision": "allow",
                            "path": "**",
                        }
                    ],
                },
            )
        )
        svc = LLMPermissionService(config_svc)
        ctx = PermissionCheckContext(category="file_write", path="backend/.env")
        result = await svc.check(ctx)
        assert result["decision"] == "deny"

    async def test_terminal_safe_command_allowed(self, db_session: Any) -> None:
        """TEST-1713: safe terminal command from default policy is allowed."""
        config_svc = ConfigService(db_session)
        await config_svc.create_node(
            ConfigNodeCreate(
                node_type="llm_permission",
                scope="global",
                key="default",
                name="默认策略",
                config_json=LLMPermissionService(config_svc).get_default_policy(),
            )
        )
        svc = LLMPermissionService(config_svc)
        ctx = PermissionCheckContext(category="terminal", command="pytest tests/")
        result = await svc.check(ctx)
        assert result["decision"] == "allow"

    async def test_terminal_dangerous_command_denied(self, db_session: Any) -> None:
        """TEST-1714: dangerous terminal command is denied by builtin policy."""
        config_svc = ConfigService(db_session)
        await config_svc.create_node(
            ConfigNodeCreate(
                node_type="llm_permission",
                scope="global",
                key="default",
                name="默认策略",
                config_json=LLMPermissionService(config_svc).get_default_policy(),
            )
        )
        svc = LLMPermissionService(config_svc)
        ctx = PermissionCheckContext(category="terminal", command="rm -rf /")
        result = await svc.check(ctx)
        assert result["decision"] == "deny"
