"""add_async_jobs_table

Revision ID: a1b2c3d4e5f6
Revises: 993712ccdc26
Create Date: 2026-08-15 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '993712ccdc26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'async_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=255), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('traceback', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_async_jobs_job_id'), 'async_jobs', ['job_id'], unique=True)
    op.create_index(op.f('ix_async_jobs_task_type'), 'async_jobs', ['task_type'], unique=False)
    op.create_index(op.f('ix_async_jobs_status'), 'async_jobs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_async_jobs_status'), table_name='async_jobs')
    op.drop_index(op.f('ix_async_jobs_task_type'), table_name='async_jobs')
    op.drop_index(op.f('ix_async_jobs_job_id'), table_name='async_jobs')
    op.drop_table('async_jobs')
