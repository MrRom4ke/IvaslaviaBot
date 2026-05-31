"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-29 11:21:32.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)

    # Create admins table
    op.create_table(
        'admins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admins_username'), 'admins', ['username'], unique=True)

    # Create drawings table - SQLAlchemy создаст enum автоматически
    op.create_table(
        'drawings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('drawing_type', sa.Enum('free', 'paid', name='drawing_type'), nullable=False),
        sa.Column('status', sa.Enum('upcoming', 'active', 'ready_to_draw', 'completed', name='drawing_status'), nullable=False),
        sa.Column('max_participants', sa.Integer(), nullable=False),
        sa.Column('winners_limit', sa.Integer(), nullable=False),
        sa.Column('start_at', sa.DateTime(), nullable=True),
        sa.Column('end_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drawings_status'), 'drawings', ['status'], unique=False)

    # Create applications table
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('drawing_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'payment_pending', 'payment_bill_loaded', 'payment_confirmed', 'payment_rejected', 'completed', name='application_status'), nullable=False),
        sa.Column('profile_attempts_used', sa.Integer(), nullable=False),
        sa.Column('payment_attempts_used', sa.Integer(), nullable=False),
        sa.Column('blocked_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('profile_attempts_used >= 0 AND profile_attempts_used <= 3', name='ck_profile_attempts_range'),
        sa.CheckConstraint('payment_attempts_used >= 0 AND payment_attempts_used <= 3', name='ck_payment_attempts_range'),
        sa.ForeignKeyConstraint(['drawing_id'], ['drawings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'drawing_id', name='uq_applications_user_drawing')
    )
    op.create_index(op.f('ix_applications_drawing_id'), 'applications', ['drawing_id'], unique=False)
    op.create_index(op.f('ix_applications_status'), 'applications', ['status'], unique=False)
    op.create_index(op.f('ix_applications_user_id'), 'applications', ['user_id'], unique=False)

    # Create application_evidences table
    op.create_table(
        'application_evidences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('evidence_type', sa.Enum('profile', 'payment', name='evidence_type'), nullable=False),
        sa.Column('file_key', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_application_evidences_application_id'), 'application_evidences', ['application_id'], unique=False)
    op.create_index(op.f('ix_application_evidences_evidence_type'), 'application_evidences', ['evidence_type'], unique=False)

    # Create operator_tickets table
    op.create_table(
        'operator_tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('drawing_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('open', 'in_progress', 'closed', name='ticket_status'), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['drawing_id'], ['drawings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_operator_tickets_status'), 'operator_tickets', ['status'], unique=False)
    op.create_index(op.f('ix_operator_tickets_user_id'), 'operator_tickets', ['user_id'], unique=False)

    # Create winners table
    op.create_table(
        'winners',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('drawing_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('selected_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['drawing_id'], ['drawings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('drawing_id', 'user_id', name='uq_winners_drawing_user')
    )
    op.create_index(op.f('ix_winners_drawing_id'), 'winners', ['drawing_id'], unique=False)
    op.create_index(op.f('ix_winners_user_id'), 'winners', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_winners_user_id'), table_name='winners')
    op.drop_index(op.f('ix_winners_drawing_id'), table_name='winners')
    op.drop_table('winners')
    op.drop_index(op.f('ix_operator_tickets_user_id'), table_name='operator_tickets')
    op.drop_index(op.f('ix_operator_tickets_status'), table_name='operator_tickets')
    op.drop_table('operator_tickets')
    op.drop_index(op.f('ix_application_evidences_evidence_type'), table_name='application_evidences')
    op.drop_index(op.f('ix_application_evidences_application_id'), table_name='application_evidences')
    op.drop_table('application_evidences')
    op.drop_index(op.f('ix_applications_user_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_status'), table_name='applications')
    op.drop_index(op.f('ix_applications_drawing_id'), table_name='applications')
    op.drop_table('applications')
    op.drop_index(op.f('ix_drawings_status'), table_name='drawings')
    op.drop_table('drawings')
    op.drop_index(op.f('ix_admins_username'), table_name='admins')
    op.drop_table('admins')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_table('users')
    op.execute("DROP TYPE ticket_status")
    op.execute("DROP TYPE evidence_type")
    op.execute("DROP TYPE application_status")
    op.execute("DROP TYPE drawing_status")
    op.execute("DROP TYPE drawing_type")
