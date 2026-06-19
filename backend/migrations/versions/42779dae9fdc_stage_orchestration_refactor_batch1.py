"""stage_orchestration_refactor_batch1

Revision ID: 42779dae9fdc
Revises: 73bb1cf05dce
Create Date: 2026-06-16 07:00:44.652973

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "42779dae9fdc"
down_revision: str | None = "73bb1cf05dce"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply Batch 1 schema changes for stage orchestration refactor."""
    # New tables
    op.create_table(
        "stage_rollback_logs",
        sa.Column("log_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("from_stage_id", sa.String(length=36), nullable=False),
        sa.Column("to_stage_id", sa.String(length=36), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("stale_artifact_ids", sa.Text(), nullable=True),
        sa.Column("git_snapshot_ref", sa.String(length=128), nullable=True),
        sa.Column("operator_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("log_id"),
    )
    op.create_index(
        "ix_stage_rollback_logs_project",
        "stage_rollback_logs",
        ["project_id"],
        unique=False,
    )

    op.create_table(
        "stage_skill_bindings",
        sa.Column("binding_id", sa.String(length=36), nullable=False),
        sa.Column("project_stage_id", sa.String(length=36), nullable=False),
        sa.Column("skill_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("execution_order", sa.Integer(), nullable=False),
        sa.Column("is_optional", sa.Boolean(), nullable=False),
        sa.Column("config_snapshot", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "role IN ('primary', 'auxiliary')", name="ck_stage_skill_binding_role"
        ),
        sa.ForeignKeyConstraint(
            ["project_stage_id"],
            ["project_stages.project_stage_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("binding_id"),
    )
    op.create_index(
        "ix_stage_skill_bindings_skill",
        "stage_skill_bindings",
        ["skill_id"],
        unique=False,
    )
    op.create_index(
        "ix_stage_skill_bindings_stage",
        "stage_skill_bindings",
        ["project_stage_id"],
        unique=False,
    )

    op.create_table(
        "project_path_config",
        sa.Column("config_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("template_level", sa.String(length=16), nullable=False),
        sa.Column("execution_strategy", sa.String(length=16), nullable=False),
        sa.Column("merge_policy_json", sa.Text(), nullable=False),
        sa.Column("selected_at", sa.DateTime(), nullable=False),
        sa.Column("selected_by", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "execution_strategy IN ('full_auto', 'semi_auto', 'full_manual')",
            name="ck_project_path_config_execution_strategy",
        ),
        sa.CheckConstraint(
            "template_level IN ('Trivial', 'Light', 'Standard', 'Deep')",
            name="ck_project_path_config_template_level",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.project_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("config_id"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index(
        "ix_project_path_config_project",
        "project_path_config",
        ["project_id"],
        unique=False,
    )

    # Add columns to existing tables. SQLite supports ADD COLUMN with
    # NOT NULL + DEFAULT, so we add them directly with nullable=False.
    op.add_column(
        "templates",
        sa.Column(
            "default_execution_strategy",
            sa.String(length=16),
            nullable=False,
            server_default="semi_auto",
        ),
    )
    op.add_column(
        "templates",
        sa.Column("merge_policy_json", sa.Text(), nullable=True),
    )

    op.add_column(
        "template_stages",
        sa.Column(
            "business_stage_key",
            sa.String(length=32),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "template_stages",
        sa.Column(
            "is_gate_required",
            sa.Boolean(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "template_stages",
        sa.Column(
            "auto_advance",
            sa.Boolean(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "project_stages",
        sa.Column("auxiliary_skill_ids", sa.Text(), nullable=True),
    )
    op.add_column(
        "project_stages",
        sa.Column(
            "runtime_status",
            sa.String(length=16),
            nullable=False,
            server_default="not_started",
        ),
    )
    op.add_column(
        "project_stages",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "project_stages",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "project_stages",
        sa.Column("execution_strategy", sa.String(length=16), nullable=True),
    )

    op.add_column(
        "projects",
        sa.Column("current_stage_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column(
            "execution_strategy",
            sa.String(length=16),
            nullable=False,
            server_default="semi_auto",
        ),
    )
    op.add_column(
        "projects",
        sa.Column("merge_policy_json", sa.Text(), nullable=True),
    )

    op.add_column(
        "execution_plans",
        sa.Column(
            "execution_strategy",
            sa.String(length=16),
            nullable=False,
            server_default="semi_auto",
        ),
    )
    op.add_column(
        "execution_plans",
        sa.Column("dependency_matrix", sa.Text(), nullable=True),
    )

    # Refresh built-in templates: old template/stage seed data is incompatible
    # with the new 9 business-stage model. We remove the built-in rows so the
    # application seed logic can recreate them with the correct structure.
    op.execute(
        "DELETE FROM template_stages WHERE template_id IN "
        "('Trivial', 'Light', 'Standard', 'Deep')"
    )
    op.execute(
        "DELETE FROM templates WHERE template_id IN "
        "('Trivial', 'Light', 'Standard', 'Deep')"
    )

    # Data migration: ensure every existing project has a project_path_config record.
    op.execute(
        """
        INSERT INTO project_path_config (
            config_id, project_id, template_level, execution_strategy,
            merge_policy_json, selected_at
        )
        SELECT lower(hex(randomblob(18))), project_id, template_level,
               'semi_auto', '{"groups": []}', datetime('now')
        FROM projects
        WHERE project_id NOT IN (SELECT project_id FROM project_path_config)
        """
    )

    # Add CHECK constraints via batch alter (SQLite requires table recreation)
    with op.batch_alter_table("templates") as batch_op:
        batch_op.create_check_constraint(
            "ck_template_default_execution_strategy",
            "default_execution_strategy IN ('full_auto', 'semi_auto', 'full_manual')",
        )

    with op.batch_alter_table("project_stages") as batch_op:
        batch_op.create_check_constraint(
            "ck_project_stage_runtime_status",
            "runtime_status IN ('not_started', 'ready', 'in_progress', "
            "'review_pending', 'gate_pending', 'passed', 'blocked', 'skipped')",
        )

    with op.batch_alter_table("projects") as batch_op:
        batch_op.create_check_constraint(
            "ck_project_execution_strategy",
            "execution_strategy IN ('full_auto', 'semi_auto', 'full_manual')",
        )

    with op.batch_alter_table("execution_plans") as batch_op:
        batch_op.create_check_constraint(
            "ck_execution_plan_execution_strategy",
            "execution_strategy IN ('full_auto', 'semi_auto', 'full_manual')",
        )


def downgrade() -> None:
    """Revert Batch 1 schema changes."""
    with op.batch_alter_table("execution_plans") as batch_op:
        batch_op.drop_constraint(
            "ck_execution_plan_execution_strategy", type_="check"
        )
    op.drop_column("execution_plans", "dependency_matrix")
    op.drop_column("execution_plans", "execution_strategy")

    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_constraint("ck_project_execution_strategy", type_="check")
    op.drop_column("projects", "merge_policy_json")
    op.drop_column("projects", "execution_strategy")
    op.drop_column("projects", "current_stage_id")

    with op.batch_alter_table("project_stages") as batch_op:
        batch_op.drop_constraint("ck_project_stage_runtime_status", type_="check")
    op.drop_column("project_stages", "execution_strategy")
    op.drop_column("project_stages", "completed_at")
    op.drop_column("project_stages", "started_at")
    op.drop_column("project_stages", "runtime_status")
    op.drop_column("project_stages", "auxiliary_skill_ids")

    op.drop_column("template_stages", "auto_advance")
    op.drop_column("template_stages", "is_gate_required")
    op.drop_column("template_stages", "business_stage_key")

    with op.batch_alter_table("templates") as batch_op:
        batch_op.drop_constraint(
            "ck_template_default_execution_strategy", type_="check"
        )
    op.drop_column("templates", "merge_policy_json")
    op.drop_column("templates", "default_execution_strategy")

    op.drop_index("ix_project_path_config_project", table_name="project_path_config")
    op.drop_table("project_path_config")
    op.drop_index("ix_stage_skill_bindings_stage", table_name="stage_skill_bindings")
    op.drop_index("ix_stage_skill_bindings_skill", table_name="stage_skill_bindings")
    op.drop_table("stage_skill_bindings")
    op.drop_index("ix_stage_rollback_logs_project", table_name="stage_rollback_logs")
    op.drop_table("stage_rollback_logs")
