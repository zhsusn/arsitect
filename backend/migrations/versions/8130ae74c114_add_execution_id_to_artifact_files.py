"""add_execution_id_to_artifact_files

Revision ID: 8130ae74c114
Revises: 28c43e14d121
Create Date: 2026-06-16 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8130ae74c114"
down_revision: str | None = "28c43e14d121"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add execution_id column to artifact_files."""
    op.add_column(
        "artifact_files",
        sa.Column(
            "execution_id",
            sa.String(length=36),
            sa.ForeignKey("skill_executions.execution_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove execution_id column from artifact_files."""
    op.drop_column("artifact_files", "execution_id")
