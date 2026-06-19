"""add_execution_tasks_and_execution_issues

Revision ID: aec5d5927d52
Revises: 8130ae74c114
Create Date: 2026-06-17 09:32:51.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = "aec5d5927d52"
down_revision: str | None = "8130ae74c114"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create execution_tasks and execution_issues tables."""
    op.create_table(
        "execution_tasks",
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("input_artifacts", sqlite.JSON(), nullable=True),
        sa.Column("assigned_skill_id", sa.String(length=36), nullable=True),
        sa.Column("parent_module", sa.String(length=64), nullable=True),
        sa.Column("output_artifact_path", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("task_id"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.project_id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "type IN ('coding', 'test', 'bugfix')",
            name="ck_execution_task_type",
        ),
        sa.CheckConstraint(
            "status IN ('not_started', 'in_progress', 'passed', 'failed', 'blocked')",
            name="ck_execution_task_status",
        ),
        sa.CheckConstraint(
            "retry_count BETWEEN 0 AND 3",
            name="ck_execution_task_retry_count",
        ),
        if_not_exists=True,
    )

    op.create_table(
        "execution_issues",
        sa.Column("issue_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("issue_type", sa.String(length=16), nullable=False),
        sa.Column("error_log", sa.Text(), nullable=True),
        sa.Column("related_artifacts", sqlite.JSON(), nullable=True),
        sa.Column("suggested_action", sa.Text(), nullable=True),
        sa.Column("feedback_to_architecture", sa.Boolean(), nullable=True, server_default="0"),
        sa.Column("target_artifact_id", sa.String(length=36), nullable=True),
        sa.Column("change_request_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("issue_id"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.project_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["execution_tasks.task_id"],
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "issue_type IN ('compile_error', 'test_failure', 'arch_mismatch', 'interface_mismatch', 'other')",
            name="ck_execution_issue_type",
        ),
        sa.CheckConstraint(
            "status IN ('open', 'resolved', 'closed')",
            name="ck_execution_issue_status",
        ),
        if_not_exists=True,
    )


def downgrade() -> None:
    """Drop execution_tasks and execution_issues tables."""
    op.drop_table("execution_issues")
    op.drop_table("execution_tasks")
