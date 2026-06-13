"""drop_c4_dsl_store_add_baseline_version

Revision ID: 1427fce328a4
Revises: 81d6fdeacf5b
Create Date: 2026-06-10 20:01:52.991680

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1427fce328a4'
down_revision: str | None = '81d6fdeacf5b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop old per-level C4 DSL store table
    op.drop_table('c4_dsl_stores')

    # Update wireframes table: replace c4_dsl_store_id with c4_baseline_version
    # and add new columns introduced by the unified YAML migration
    op.add_column(
        'wireframes',
        sa.Column('c4_baseline_version', sa.String(length=20), nullable=True, comment='关联的 C4 Baseline 版本'),
    )
    op.add_column(
        'wireframes',
        sa.Column('pipeline_stage', sa.String(length=16), nullable=False, server_default='idle'),
    )
    op.add_column(
        'wireframes',
        sa.Column('page_count', sa.Integer(), nullable=True, comment='生成页面数'),
    )
    op.add_column(
        'wireframes',
        sa.Column('avg_confidence', sa.Integer(), nullable=True, comment='平均映射置信度'),
    )
    op.drop_column('wireframes', 'edges')
    op.drop_column('wireframes', 'nodes')


def downgrade() -> None:
    # Restore wireframes columns
    op.add_column('wireframes', sa.Column('nodes', sa.TEXT(), nullable=False))
    op.add_column('wireframes', sa.Column('edges', sa.TEXT(), nullable=False))
    op.drop_column('wireframes', 'avg_confidence')
    op.drop_column('wireframes', 'page_count')
    op.drop_column('wireframes', 'pipeline_stage')
    op.drop_column('wireframes', 'c4_baseline_version')

    # Restore c4_dsl_stores table
    op.create_table(
        'c4_dsl_stores',
        sa.Column('store_id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('project_id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('level', sa.VARCHAR(length=2), nullable=False),
        sa.Column('dsl_text', sa.TEXT(), nullable=True),
        sa.Column('generation_mode', sa.VARCHAR(length=8), nullable=True),
        sa.Column('confidence', sa.FLOAT(), nullable=True),
        sa.Column('created_at', sa.DATETIME(), nullable=False),
        sa.Column('updated_at', sa.DATETIME(), nullable=False),
        sa.Column('is_manual', sa.BOOLEAN(), server_default=sa.text("'0'"), nullable=False),
        sa.CheckConstraint("generation_mode IS NULL OR generation_mode IN ('auto','manual')", name=op.f('ck_c4_generation_mode')),
        sa.CheckConstraint("level IN ('L1','L2','L3','L4')", name=op.f('ck_c4_level')),
        sa.CheckConstraint('confidence IS NULL OR (confidence >= 0 AND confidence <= 1)', name=op.f('ck_c4_confidence')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('store_id'),
    )
