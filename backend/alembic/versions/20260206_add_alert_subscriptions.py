"""Add alert_subscriptions table

Revision ID: 20260206_subscriptions
Revises: 20260205_add_celex_id_to_documents
Create Date: 2026-02-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260206_subscriptions'
down_revision = '20260205_add_celex_id_to_documents'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'alert_subscriptions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('subscription_name', sa.String(200), nullable=False, server_default='Mon abonnement'),
        sa.Column('event_types', sa.JSON(), nullable=False, server_default='["all"]'),
        sa.Column('supplier_ids', sa.JSON(), nullable=True),
        sa.Column('supplier_names', sa.JSON(), nullable=True),
        sa.Column('site_ids', sa.JSON(), nullable=True),
        sa.Column('site_names', sa.JSON(), nullable=True),
        sa.Column('countries', sa.JSON(), nullable=True),
        sa.Column('min_criticality', sa.String(20), nullable=False, server_default='MOYEN'),
        sa.Column('notify_immediately', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('digest_frequency', sa.String(20), nullable=True),
        sa.Column('include_weather_alerts', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('include_regulatory', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('include_geopolitical', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('verification_token', sa.String(100), nullable=True),
        sa.Column('last_notified_at', sa.DateTime(), nullable=True),
        sa.Column('notification_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    
    # Index on email for faster lookups
    op.create_index('ix_alert_subscriptions_email', 'alert_subscriptions', ['email'])
    op.create_index('ix_alert_subscriptions_is_active', 'alert_subscriptions', ['is_active'])


def downgrade() -> None:
    op.drop_index('ix_alert_subscriptions_is_active', table_name='alert_subscriptions')
    op.drop_index('ix_alert_subscriptions_email', table_name='alert_subscriptions')
    op.drop_table('alert_subscriptions')
