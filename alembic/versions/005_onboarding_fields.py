"""onboarding_fields

Revision ID: 005
Revises: 004
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_onboarded', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_goals', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('user_goals', sa.Column('height_cm', sa.Float(), nullable=True))
    op.add_column('user_goals', sa.Column('current_weight_kg', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('user_goals', 'current_weight_kg')
    op.drop_column('user_goals', 'height_cm')
    op.drop_column('user_goals', 'age')
    op.drop_column('users', 'is_onboarded')
