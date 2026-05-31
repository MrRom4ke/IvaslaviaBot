"""fix telegram_id to bigint

Revision ID: 002
Revises: 001
Create Date: 2026-05-31 12:19:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Изменяем тип колонки telegram_id с INTEGER на BIGINT
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)


def downgrade():
    # Возвращаем обратно на INTEGER (может привести к потере данных!)
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False)
