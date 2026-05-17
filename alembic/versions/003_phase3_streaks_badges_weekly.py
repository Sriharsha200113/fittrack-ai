"""phase3_streaks_badges_weekly

Revision ID: 003
Revises: 002
Create Date: 2025-01-01 00:00:02.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_streaks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_active_date', sa.Date(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'user_badges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('badge_slug', sa.String(50), nullable=False),
        sa.Column('earned_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'badge_slug', name='uq_user_badge'),
    )

    op.create_table(
        'weekly_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id'), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('week_end', sa.Date(), nullable=False),
        sa.Column('rankings', postgresql.JSON(), nullable=False),
        sa.Column('winner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index('ix_user_streaks_user_id', 'user_streaks', ['user_id'])
    op.create_index('ix_user_badges_user_id', 'user_badges', ['user_id'])
    op.create_index('ix_weekly_snapshots_squad_week', 'weekly_snapshots', ['squad_id', 'week_start'])


def downgrade() -> None:
    op.drop_index('ix_weekly_snapshots_squad_week', 'weekly_snapshots')
    op.drop_index('ix_user_badges_user_id', 'user_badges')
    op.drop_index('ix_user_streaks_user_id', 'user_streaks')
    op.drop_table('weekly_snapshots')
    op.drop_table('user_badges')
    op.drop_table('user_streaks')
