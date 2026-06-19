"""stage_orchestration_refactor_batch2

Revision ID: 28c43e14d121
Revises: 42779dae9fdc
Create Date: 2026-06-16 09:19:36.702149

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "28c43e14d121"
down_revision: str | None = "42779dae9fdc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add runtime gate/advance flags to project_stages."""
    op.add_column(
        "project_stages",
        sa.Column("is_gate_required", sa.Boolean(), nullable=False, server_default="1"),
    )
    op.add_column(
        "project_stages",
        sa.Column("auto_advance", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Remove runtime gate/advance flags from project_stages."""
    op.drop_column("project_stages", "auto_advance")
    op.drop_column("project_stages", "is_gate_required")
