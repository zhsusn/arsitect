"""add_config_nodes

Revision ID: 9ce34a2c3035
Revises: 3669614ad7de
Create Date: 2026-06-14 12:15:26.904131

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = "9ce34a2c3035"
down_revision: str | None = "3669614ad7de"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "config_nodes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("node_type", sa.String(length=50), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("scope_target", sa.String(length=36), nullable=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("config_json", sqlite.JSON(), nullable=False, server_default="{}"),
        sa.Column("secret_json", sqlite.JSON(), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "node_type",
            "scope",
            "scope_target",
            "key",
            name="uq_config_node_type_scope_target_key",
        ),
        sa.CheckConstraint(
            "scope IN ('managed','global','project','user')",
            name="ck_config_node_scope",
        ),
        sa.CheckConstraint(
            "node_type IN ('llm_provider','llm_permission','security_policy','notification')",
            name="ck_config_node_type",
        ),
    )
    op.create_index(op.f("ix_config_nodes_node_type"), "config_nodes", ["node_type"], unique=False)
    op.create_index(op.f("ix_config_nodes_scope"), "config_nodes", ["scope"], unique=False)
    op.create_index(
        op.f("ix_config_nodes_scope_target"), "config_nodes", ["scope_target"], unique=False
    )
    op.create_index(op.f("ix_config_nodes_key"), "config_nodes", ["key"], unique=False)
    op.create_index(
        "ix_config_node_type_scope_enabled",
        "config_nodes",
        ["node_type", "scope", "is_enabled"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_config_node_type_scope_enabled", table_name="config_nodes")
    op.drop_index(op.f("ix_config_nodes_key"), table_name="config_nodes")
    op.drop_index(op.f("ix_config_nodes_scope_target"), table_name="config_nodes")
    op.drop_index(op.f("ix_config_nodes_scope"), table_name="config_nodes")
    op.drop_index(op.f("ix_config_nodes_node_type"), table_name="config_nodes")
    op.drop_table("config_nodes")
