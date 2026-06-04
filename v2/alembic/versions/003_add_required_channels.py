"""add required channels table

Revision ID: 003
Revises: 002
Create Date: 2026-06-02 16:54:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create required_channels table
    op.create_table(
        'required_channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('drawing_id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.BigInteger(), nullable=False),
        sa.Column('channel_username', sa.String(length=255), nullable=True),
        sa.Column('channel_title', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['drawing_id'], ['drawings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_required_channels_drawing_id'), 'required_channels', ['drawing_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_required_channels_drawing_id'), table_name='required_channels')
    op.drop_table('required_channels')
