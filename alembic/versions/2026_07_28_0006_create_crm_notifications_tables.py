"""Create CRM, notifications, support and integrations tables

Revision ID: 2026_07_28_0006
Revises: 2026_07_28_0005
Create Date: 2026-07-28 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_07_28_0006"
down_revision: Union[str, None] = "2026_07_28_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create leads table
    op.create_table(
        'leads',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('assigned_to', sa.String(length=36), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('interested_plan_id', sa.String(length=36), nullable=True),
        sa.Column('preferred_time', sa.String(length=100), nullable=True),
        sa.Column('stage', sa.String(length=30), nullable=False, server_default='NEW'),
        sa.Column('next_follow_up_at', sa.DateTime(), nullable=True),
        sa.Column('lost_reason', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('converted_member_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_leads_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_leads_branch_id'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], name='fk_leads_assigned_to'),
        sa.ForeignKeyConstraint(['interested_plan_id'], ['membership_plans.id'], name='fk_leads_plan_id'),
        sa.ForeignKeyConstraint(['converted_member_id'], ['members.id'], name='fk_leads_converted_member_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_leads_branch_stage', 'leads', ['branch_id', 'stage'])
    op.create_index('ix_leads_follow_up', 'leads', ['tenant_id', 'next_follow_up_at', 'stage'])
    op.create_index('ix_leads_phone', 'leads', ['tenant_id', 'phone'])

    # Create lead_follow_ups table
    op.create_table(
        'lead_follow_ups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('lead_id', sa.String(length=36), nullable=False),
        sa.Column('performed_by', sa.String(length=36), nullable=False),
        sa.Column('follow_up_type', sa.String(length=20), nullable=False),
        sa.Column('outcome', sa.String(length=500), nullable=True),
        sa.Column('next_follow_up_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_lead_follow_ups_tenant_id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name='fk_lead_follow_ups_lead_id'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], name='fk_lead_follow_ups_performed_by'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lead_follow_ups_lead_date', 'lead_follow_ups', ['lead_id', 'created_at'])

    # Create trial_passes table
    op.create_table(
        'trial_passes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('lead_id', sa.String(length=36), nullable=False),
        sa.Column('pass_code', sa.String(length=60), nullable=False),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('valid_until', sa.DateTime(), nullable=False),
        sa.Column('max_visits', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('used_visits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_trial_passes_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_trial_passes_branch_id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name='fk_trial_passes_lead_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'pass_code', name='uq_trial_passes_tenant_code')
    )
    op.create_index('ix_trial_passes_lead_status', 'trial_passes', ['lead_id', 'status'])

    # Create message_templates table
    op.create_table(
        'message_templates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('template_code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('subject_template', sa.String(length=255), nullable=True),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_message_templates_tenant_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'template_code', name='uq_message_templates_tenant_code')
    )

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('member_id', sa.String(length=36), nullable=True),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('message_body', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=100), nullable=False),
        sa.Column('reference_type', sa.String(length=100), nullable=True),
        sa.Column('reference_id', sa.String(length=36), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='QUEUED'),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('failure_reason', sa.String(length=1000), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_notifications_tenant_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_notifications_user_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_notifications_member_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_status_schedule', 'notifications', ['status', 'scheduled_at'])
    op.create_index('ix_notifications_member_date', 'notifications', ['member_id', 'created_at'])

    # Create support_tickets table
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('raised_by', sa.String(length=36), nullable=False),
        sa.Column('assigned_to', sa.String(length=36), nullable=True),
        sa.Column('ticket_number', sa.String(length=60), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='OPEN'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_support_tickets_tenant_id'),
        sa.ForeignKeyConstraint(['raised_by'], ['users.id'], name='fk_support_tickets_raised_by'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], name='fk_support_tickets_assigned_to'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'ticket_number', name='uq_support_tickets_tenant_number')
    )
    op.create_index('ix_support_tickets_tenant_status', 'support_tickets', ['tenant_id', 'status', 'priority'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('branch_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('old_values_json', sa.JSON(), nullable=True),
        sa.Column('new_values_json', sa.JSON(), nullable=True),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_audit_logs_tenant_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_audit_logs_user_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_audit_logs_branch_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_tenant_date', 'audit_logs', ['tenant_id', 'created_at'])
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_logs_user_date', 'audit_logs', ['user_id', 'created_at'])

    # Create integration_configs table
    op.create_table(
        'integration_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('integration_type', sa.String(length=100), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('config_encrypted', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('last_tested_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_integration_configs_tenant_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'integration_type', 'provider_name', name='uq_integration_configs_tenant_type')
    )

    # Create webhook_events table
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=True),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('event_id', sa.String(length=200), nullable=False),
        sa.Column('event_type', sa.String(length=150), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=False),
        sa.Column('signature_valid', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('processing_status', sa.String(length=20), nullable=False, server_default='RECEIVED'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_webhook_events_tenant_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_name', 'event_id', name='uq_webhook_events_provider_event')
    )
    op.create_index('ix_webhook_events_status_date', 'webhook_events', ['processing_status', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_webhook_events_status_date', table_name='webhook_events')
    op.drop_table('webhook_events')
    op.drop_table('integration_configs')
    op.drop_index('ix_audit_logs_user_date', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity', table_name='audit_logs')
    op.drop_index('ix_audit_logs_tenant_date', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('ix_support_tickets_tenant_status', table_name='support_tickets')
    op.drop_table('support_tickets')
    op.drop_index('ix_notifications_member_date', table_name='notifications')
    op.drop_index('ix_notifications_status_schedule', table_name='notifications')
    op.drop_table('notifications')
    op.drop_table('message_templates')
    op.drop_index('ix_trial_passes_lead_status', table_name='trial_passes')
    op.drop_table('trial_passes')
    op.drop_index('ix_lead_follow_ups_lead_date', table_name='lead_follow_ups')
    op.drop_table('lead_follow_ups')
    op.drop_index('ix_leads_phone', table_name='leads')
    op.drop_index('ix_leads_follow_up', table_name='leads')
    op.drop_index('ix_leads_branch_stage', table_name='leads')
    op.drop_table('leads')
