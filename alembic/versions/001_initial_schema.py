"""initial_schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('phone', sa.String(20), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )

    op.create_table(
        'squads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('invite_code', sa.String(10), nullable=False, unique=True),
        sa.Column('wa_group_id', sa.String(200), nullable=False, unique=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'squad_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('role', sa.String(20), nullable=False, server_default='member'),
    )

    op.create_table(
        'meal_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('meal_type', sa.String(20), nullable=True),
        sa.Column('food_items', postgresql.JSON(), nullable=True),
        sa.Column('calories', sa.Float(), nullable=True),
        sa.Column('protein_g', sa.Float(), nullable=True),
        sa.Column('carbs_g', sa.Float(), nullable=True),
        sa.Column('fat_g', sa.Float(), nullable=True),
        sa.Column('logged_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('log_date', sa.Date(), nullable=False, server_default=sa.func.current_date()),
    )

    op.create_table(
        'exercise_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('workout_type', sa.String(50), nullable=True),
        sa.Column('duration_min', sa.Integer(), nullable=True),
        sa.Column('sets_reps', postgresql.JSON(), nullable=True),
        sa.Column('calories_burned', sa.Float(), nullable=True),
        sa.Column('logged_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('log_date', sa.Date(), nullable=False, server_default=sa.func.current_date()),
    )

    op.create_table(
        'daily_points',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column('points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('meals_logged', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('workouts_logged', sa.Integer(), nullable=False, server_default='0'),
    )

    # Indexes for common query patterns
    op.create_index('ix_meal_logs_user_date', 'meal_logs', ['user_id', 'log_date'])
    op.create_index('ix_exercise_logs_user_date', 'exercise_logs', ['user_id', 'log_date'])
    op.create_index('ix_daily_points_squad_date', 'daily_points', ['squad_id', 'date'])
    op.create_index('ix_daily_points_user_squad_date', 'daily_points', ['user_id', 'squad_id', 'date'], unique=True)


def downgrade() -> None:
    op.drop_table('daily_points')
    op.drop_table('exercise_logs')
    op.drop_table('meal_logs')
    op.drop_table('squad_members')
    op.drop_table('squads')
    op.drop_table('users')
