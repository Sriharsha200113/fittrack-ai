"""phase2_goals_metrics

Revision ID: 002
Revises: 001
Create Date: 2025-01-01 00:00:01.000000

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('daily_calories', sa.Integer(), nullable=False, server_default='2000'),
        sa.Column('protein_g', sa.Integer(), nullable=False, server_default='150'),
        sa.Column('carbs_g', sa.Integer(), nullable=True),
        sa.Column('fat_g', sa.Integer(), nullable=True),
        sa.Column('goal_type', sa.String(20), nullable=False, server_default='maintain'),
        sa.Column('target_weight_kg', sa.Float(), nullable=True),
        sa.Column('activity_level', sa.String(20), nullable=False, server_default='moderate'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'body_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('body_fat_pct', sa.Float(), nullable=True),
        sa.Column('muscle_mass_kg', sa.Float(), nullable=True),
        sa.Column('waist_cm', sa.Float(), nullable=True),
        sa.Column('chest_cm', sa.Float(), nullable=True),
        sa.Column('arms_cm', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('logged_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('log_date', sa.Date(), nullable=False, server_default=sa.func.current_date()),
    )

    op.add_column('daily_points', sa.Column('protein_hit', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('daily_points', sa.Column('calorie_target_hit', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('daily_points', sa.Column('weight_logged', sa.Boolean(), nullable=False, server_default='false'))

    op.create_index('ix_body_metrics_user_date', 'body_metrics', ['user_id', 'log_date'])


def downgrade() -> None:
    op.drop_index('ix_body_metrics_user_date', 'body_metrics')
    op.drop_column('daily_points', 'weight_logged')
    op.drop_column('daily_points', 'calorie_target_hit')
    op.drop_column('daily_points', 'protein_hit')
    op.drop_table('body_metrics')
    op.drop_table('user_goals')
