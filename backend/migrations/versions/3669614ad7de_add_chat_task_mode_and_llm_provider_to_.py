"""add_chat_task_mode_and_llm_provider_to_cli_session

Revision ID: 3669614ad7de
Revises: c013016fecf7
Create Date: 2026-06-13 17:06:03.763800

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '3669614ad7de'
down_revision: str | None = 'c013016fecf7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add chat-oriented columns to cli_sessions.
    op.add_column(
        'cli_sessions',
        sa.Column(
            'task_mode',
            sa.String(length=20),
            nullable=False,
            server_default='free-chat',
        ),
    )
    op.add_column(
        'cli_sessions',
        sa.Column('llm_provider', sa.String(length=20), nullable=True),
    )
    op.add_column(
        'cli_sessions',
        sa.Column('context_json', sqlite.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('cli_sessions', 'context_json')
    op.drop_column('cli_sessions', 'llm_provider')
    op.drop_column('cli_sessions', 'task_mode')
