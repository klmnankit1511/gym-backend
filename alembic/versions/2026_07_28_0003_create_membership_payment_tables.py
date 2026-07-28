"""Create membership plans, subscriptions, invoices and payments

Revision ID: 2026_07_28_0003
Revises: 2026_07_28_0002
Create Date: 2026-07-28 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_07_28_0003"
down_revision: Union[str, None] = "2026_07_28_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create membership_plans table
    op.create_table(
        'membership_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=True),
        sa.Column('plan_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('plan_type', sa.String(length=30), nullable=False),
        sa.Column('duration_value', sa.Integer(), nullable=True),
        sa.Column('duration_unit', sa.String(length=10), nullable=True),
        sa.Column('visit_limit', sa.Integer(), nullable=True),
        sa.Column('class_limit', sa.Integer(), nullable=True),
        sa.Column('pt_session_limit', sa.Integer(), nullable=True),
        sa.Column('base_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('joining_fee', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('tax_percent', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0'),
        sa.Column('freeze_allowed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('max_freeze_days', sa.Integer(), nullable=True),
        sa.Column('grace_period_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('auto_renew_allowed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('cross_branch_access', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_membership_plans_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_membership_plans_branch_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'plan_code', name='uq_membership_plans_tenant_code')
    )
    op.create_index('ix_membership_plans_branch_status', 'membership_plans', ['branch_id', 'status'])

    # Create member_subscriptions table
    op.create_table(
        'member_subscriptions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('membership_plan_id', sa.String(length=36), nullable=False),
        sa.Column('subscription_number', sa.String(length=60), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('original_end_date', sa.Date(), nullable=False),
        sa.Column('sale_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('final_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('remaining_visits', sa.Integer(), nullable=True),
        sa.Column('remaining_classes', sa.Integer(), nullable=True),
        sa.Column('remaining_pt_sessions', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('cancellation_reason', sa.String(length=500), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_member_subscriptions_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_member_subscriptions_branch_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_member_subscriptions_member_id'),
        sa.ForeignKeyConstraint(['membership_plan_id'], ['membership_plans.id'], name='fk_member_subscriptions_plan_id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_member_subscriptions_created_by'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'subscription_number', name='uq_member_subscriptions_number')
    )
    op.create_index('ix_member_subscriptions_member_status', 'member_subscriptions', ['member_id', 'status'])
    op.create_index('ix_member_subscriptions_expiry', 'member_subscriptions', ['tenant_id', 'branch_id', 'end_date', 'status'])

    # Create subscription_freezes table
    op.create_table(
        'subscription_freezes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('subscription_id', sa.String(length=36), nullable=False),
        sa.Column('freeze_start_date', sa.Date(), nullable=False),
        sa.Column('freeze_end_date', sa.Date(), nullable=False),
        sa.Column('total_days', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='REQUESTED'),
        sa.Column('requested_by', sa.String(length=36), nullable=False),
        sa.Column('approved_by', sa.String(length=36), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_subscription_freezes_tenant_id'),
        sa.ForeignKeyConstraint(['subscription_id'], ['member_subscriptions.id'], name='fk_subscription_freezes_subscription_id'),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], name='fk_subscription_freezes_requested_by'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], name='fk_subscription_freezes_approved_by'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_subscription_freezes_subscription_status', 'subscription_freezes', ['subscription_id', 'status'])

    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('subscription_id', sa.String(length=36), nullable=True),
        sa.Column('invoice_number', sa.String(length=60), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('subtotal_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('paid_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('balance_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ISSUED'),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_invoices_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_invoices_branch_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_invoices_member_id'),
        sa.ForeignKeyConstraint(['subscription_id'], ['member_subscriptions.id'], name='fk_invoices_subscription_id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_invoices_created_by'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'invoice_number', name='uq_invoices_tenant_number')
    )
    op.create_index('ix_invoices_member_status', 'invoices', ['member_id', 'status'])
    op.create_index('ix_invoices_branch_date', 'invoices', ['branch_id', 'invoice_date'])
    op.create_index('ix_invoices_due_status', 'invoices', ['tenant_id', 'due_date', 'status'])

    # Create invoice_items table
    op.create_table(
        'invoice_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('tax_percent', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('line_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], name='fk_invoice_items_invoice_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_invoice_items_invoice', 'invoice_items', ['invoice_id'])

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=True),
        sa.Column('payment_number', sa.String(length=60), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('gateway_name', sa.String(length=100), nullable=True),
        sa.Column('gateway_transaction_id', sa.String(length=150), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('reference_number', sa.String(length=150), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('collected_by', sa.String(length=36), nullable=True),
        sa.Column('idempotency_key', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_payments_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_payments_branch_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_payments_member_id'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], name='fk_payments_invoice_id'),
        sa.ForeignKeyConstraint(['collected_by'], ['users.id'], name='fk_payments_collected_by'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'payment_number', name='uq_payments_tenant_number'),
        sa.UniqueConstraint('tenant_id', 'idempotency_key', name='uq_payments_idempotency')
    )
    op.create_index('ix_payments_invoice_status', 'payments', ['invoice_id', 'status'])
    op.create_index('ix_payments_branch_date', 'payments', ['branch_id', 'payment_date'])
    op.create_index('ix_payments_gateway_transaction', 'payments', ['gateway_transaction_id'])

    # Create refunds table
    op.create_table(
        'refunds',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('payment_id', sa.String(length=36), nullable=False),
        sa.Column('refund_number', sa.String(length=60), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=False),
        sa.Column('gateway_refund_id', sa.String(length=150), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='REQUESTED'),
        sa.Column('requested_by', sa.String(length=36), nullable=False),
        sa.Column('approved_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_refunds_tenant_id'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], name='fk_refunds_payment_id'),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], name='fk_refunds_requested_by'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], name='fk_refunds_approved_by'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'refund_number', name='uq_refunds_tenant_number')
    )
    op.create_index('ix_refunds_payment_status', 'refunds', ['payment_id', 'status'])


def downgrade() -> None:
    op.drop_index('ix_refunds_payment_status', table_name='refunds')
    op.drop_table('refunds')
    op.drop_index('ix_payments_gateway_transaction', table_name='payments')
    op.drop_index('ix_payments_branch_date', table_name='payments')
    op.drop_index('ix_payments_invoice_status', table_name='payments')
    op.drop_table('payments')
    op.drop_index('ix_invoice_items_invoice', table_name='invoice_items')
    op.drop_table('invoice_items')
    op.drop_index('ix_invoices_due_status', table_name='invoices')
    op.drop_index('ix_invoices_branch_date', table_name='invoices')
    op.drop_index('ix_invoices_member_status', table_name='invoices')
    op.drop_table('invoices')
    op.drop_index('ix_subscription_freezes_subscription_status', table_name='subscription_freezes')
    op.drop_table('subscription_freezes')
    op.drop_index('ix_member_subscriptions_expiry', table_name='member_subscriptions')
    op.drop_index('ix_member_subscriptions_member_status', table_name='member_subscriptions')
    op.drop_table('member_subscriptions')
    op.drop_index('ix_membership_plans_branch_status', table_name='membership_plans')
    op.drop_table('membership_plans')
