"""add_llm_tables

Revision ID: 73bb1cf05dce
Revises: 9ce34a2c3035
Create Date: 2026-06-14 18:45:24.348913

"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = "73bb1cf05dce"
down_revision: str | None = "9ce34a2c3035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create dedicated LLM tables and migrate existing config_nodes data."""
    # Create policy_templates table.
    op.create_table(
        "policy_templates",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_mode", sa.String(length=10), nullable=False),
        sa.Column("rules_json", sqlite.JSON(), nullable=False, server_default="[]"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )

    # Create llm_providers table.
    op.create_table(
        "llm_providers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("scope_target", sa.String(length=36), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_type", sa.String(length=20), nullable=False),
        sa.Column("config_json", sqlite.JSON(), nullable=False, server_default="{}"),
        sa.Column("secret_json", sqlite.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "scope",
            "scope_target",
            "key",
            name="uq_llm_provider_scope_target_key",
        ),
        if_not_exists=True,
    )
    op.create_index(op.f("ix_llm_providers_scope"), "llm_providers", ["scope"], unique=False, if_not_exists=True)
    op.create_index(
        op.f("ix_llm_providers_scope_target"), "llm_providers", ["scope_target"], unique=False, if_not_exists=True
    )
    op.create_index(op.f("ix_llm_providers_key"), "llm_providers", ["key"], unique=False, if_not_exists=True)
    op.create_index(
        "ix_llm_provider_is_default_scope",
        "llm_providers",
        ["is_default", "scope"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index("ix_llm_provider_is_enabled", "llm_providers", ["is_enabled"], unique=False, if_not_exists=True)

    # Create llm_policies table.
    op.create_table(
        "llm_policies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("scope_target", sa.String(length=36), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("default_mode", sa.String(length=10), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_id", sa.String(length=32), nullable=True),
        sa.Column("is_customized", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["policy_templates.id"],
        ),
        sa.UniqueConstraint(
            "scope",
            "scope_target",
            "key",
            name="uq_llm_policy_scope_target_key",
        ),
        if_not_exists=True,
    )
    op.create_index(op.f("ix_llm_policies_scope"), "llm_policies", ["scope"], unique=False, if_not_exists=True)
    op.create_index(
        op.f("ix_llm_policies_scope_target"), "llm_policies", ["scope_target"], unique=False, if_not_exists=True
    )
    op.create_index(op.f("ix_llm_policies_key"), "llm_policies", ["key"], unique=False, if_not_exists=True)
    op.create_index("ix_llm_policy_template_id", "llm_policies", ["template_id"], unique=False, if_not_exists=True)
    op.create_index("ix_llm_policy_is_enabled", "llm_policies", ["is_enabled"], unique=False, if_not_exists=True)

    # Create llm_policy_rules table.
    op.create_table(
        "llm_policy_rules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("policy_id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("action_type", sa.String(length=20), nullable=False),
        sa.Column("permission", sa.String(length=10), nullable=False),
        sa.Column("pattern", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("extra_json", sqlite.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["policy_id"], ["llm_policies.id"], ondelete="CASCADE"),
        if_not_exists=True,
    )
    op.create_index(
        "ix_llm_policy_rule_policy_category_sort",
        "llm_policy_rules",
        ["policy_id", "category", "sort_order"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        op.f("ix_llm_policy_rules_action_type"),
        "llm_policy_rules",
        ["action_type"],
        unique=False,
        if_not_exists=True,
    )

    # Migrate existing config_nodes data.
    _migrate_llm_providers()
    _migrate_llm_policies()


def _load_json(value: Any) -> Any:
    """Parse a JSON string or return the value if already decoded."""
    import json

    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value


def _migrate_llm_providers() -> None:
    """Copy llm_provider config_nodes into llm_providers."""
    conn = op.get_bind()
    rows = (
        conn.execute(
            sa.text(
                """
            SELECT id, name, key, scope, scope_target, priority,
                   config_json, secret_json, description,
                   is_default, is_enabled, created_at, updated_at
            FROM config_nodes
            WHERE node_type = 'llm_provider'
            """
            )
        )
        .mappings()
        .all()
    )

    for row in rows:
        config_json = _load_json(row["config_json"]) or {}
        provider_type = "kimi-cli"
        if isinstance(config_json, dict):
            provider_type = str(config_json.get("provider", "kimi-cli")).lower()
            if provider_type == "kimi":
                provider_type = "kimi-cli"

        conn.execute(
            sa.text(
                """
                INSERT INTO llm_providers (
                    id, name, key, scope, scope_target, priority,
                    provider_type, config_json, secret_json, description,
                    is_default, is_enabled, created_at, updated_at
                ) VALUES (
                    :id, :name, :key, :scope, :scope_target, :priority,
                    :provider_type, :config_json, :secret_json, :description,
                    :is_default, :is_enabled, :created_at, :updated_at
                )
                """
            ),
            {
                "id": row["id"],
                "name": row["name"],
                "key": row["key"],
                "scope": row["scope"],
                "scope_target": row["scope_target"],
                "priority": row["priority"],
                "provider_type": provider_type,
                "config_json": _to_json(config_json),
                "secret_json": _to_json(row["secret_json"]),
                "description": row["description"],
                "is_default": row["is_default"],
                "is_enabled": row["is_enabled"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            },
        )


def _migrate_llm_policies() -> None:
    """Copy llm_permission config_nodes into llm_policies and rules."""
    conn = op.get_bind()
    rows = (
        conn.execute(
            sa.text(
                """
            SELECT id, name, key, scope, scope_target, priority,
                   config_json, description,
                   is_default, is_enabled, created_at, updated_at
            FROM config_nodes
            WHERE node_type = 'llm_permission'
            """
            )
        )
        .mappings()
        .all()
    )

    for row in rows:
        config_json = _load_json(row["config_json"]) or {}
        default_mode = "ask"
        rules: list[dict[str, Any]] = []
        if isinstance(config_json, dict):
            default_mode = config_json.get("default_mode", "ask") or "ask"
            rules = list(config_json.get("rules", []) or [])

        conn.execute(
            sa.text(
                """
                INSERT INTO llm_policies (
                    id, name, key, scope, scope_target, priority,
                    default_mode, description, template_id,
                    is_customized, is_enabled, created_at, updated_at
                ) VALUES (
                    :id, :name, :key, :scope, :scope_target, :priority,
                    :default_mode, :description, NULL,
                    0, :is_enabled, :created_at, :updated_at
                )
                """
            ),
            {
                "id": row["id"],
                "name": row["name"],
                "key": row["key"],
                "scope": row["scope"],
                "scope_target": row["scope_target"],
                "priority": row["priority"],
                "default_mode": default_mode,
                "description": row["description"],
                "is_enabled": row["is_enabled"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            },
        )

        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                continue
            category = _infer_category(rule)
            action_type = _infer_action_type(rule, category)
            permission = rule.get("decision", "ask")
            pattern = rule.get("path") or rule.get("command") or rule.get("domain") or "*"
            conn.execute(
                sa.text(
                    """
                    INSERT INTO llm_policy_rules (
                        id, policy_id, category, action_type, permission,
                        pattern, description, sort_order, created_at, updated_at
                    ) VALUES (
                        :id, :policy_id, :category, :action_type, :permission,
                        :pattern, :description, :sort_order, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "id": _new_uuid(),
                    "policy_id": row["id"],
                    "category": category,
                    "action_type": action_type,
                    "permission": permission,
                    "pattern": pattern,
                    "description": rule.get("description"),
                    "sort_order": idx,
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                },
            )


def _infer_category(rule: dict[str, Any]) -> str:
    """Infer rule category from legacy rule dict."""
    category = rule.get("category")
    if category in {"high_risk", "file_system", "terminal", "network"}:
        return category
    action = rule.get("action_type") or rule.get("category")
    if action in {"file_read", "file_write", "file_delete"}:
        return "file_system"
    if action == "terminal":
        return "terminal"
    if action in {"web_fetch", "external_api"}:
        return "network"
    return "file_system"


def _infer_action_type(rule: dict[str, Any], category: str) -> str:
    """Infer action_type from legacy rule dict."""
    action = rule.get("action_type")
    if action:
        return action
    old_category = rule.get("category")
    if old_category in {
        "file_read",
        "file_write",
        "file_delete",
        "terminal",
        "web_fetch",
        "external_api",
    }:
        return old_category
    if category == "file_system":
        return "file_read"
    if category == "terminal":
        return "terminal"
    return "web_fetch"


def _to_json(value: Any) -> str | None:
    """Serialize value to JSON string for SQLite."""
    import json

    if value is None:
        return None
    return json.dumps(value)


def _new_uuid() -> str:
    """Generate a new UUID string."""
    import uuid

    return str(uuid.uuid4())


def downgrade() -> None:
    """Drop dedicated LLM tables."""
    op.drop_index(op.f("ix_llm_policy_rules_action_type"), table_name="llm_policy_rules")
    op.drop_index("ix_llm_policy_rule_policy_category_sort", table_name="llm_policy_rules")
    op.drop_table("llm_policy_rules")
    op.drop_index("ix_llm_policy_is_enabled", table_name="llm_policies")
    op.drop_index("ix_llm_policy_template_id", table_name="llm_policies")
    op.drop_index(op.f("ix_llm_policies_key"), table_name="llm_policies")
    op.drop_index(op.f("ix_llm_policies_scope_target"), table_name="llm_policies")
    op.drop_index(op.f("ix_llm_policies_scope"), table_name="llm_policies")
    op.drop_table("llm_policies")
    op.drop_index("ix_llm_provider_is_enabled", table_name="llm_providers")
    op.drop_index("ix_llm_provider_is_default_scope", table_name="llm_providers")
    op.drop_index(op.f("ix_llm_providers_key"), table_name="llm_providers")
    op.drop_index(op.f("ix_llm_providers_scope_target"), table_name="llm_providers")
    op.drop_index(op.f("ix_llm_providers_scope"), table_name="llm_providers")
    op.drop_table("llm_providers")
    op.drop_table("policy_templates")
