"""Create attendance and access control tables

Revision ID: 2026_07_28_0004
Revises: 2026_07_28_0003
Create Date: 2026-07-28 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_07_28_0004"
down_revision: Union[str, None] = "2026_07_28_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create access_devices table
    op.create_table(
        'access_devices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('device_code', sa.String(length=100), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ONLINE'),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_access_devices_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_access_devices_branch_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'device_code', name='uq_access_devices_tenant_code')
    )
    op.create_index('ix_access_devices_branch_status', 'access_devices', ['branch_id', 'status'])

    # Create attendance_records table
    op.create_table(
        'attendance_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('subscription_id', sa.String(length=36), nullable=True),
        sa.Column('access_device_id', sa.String(length=36), nullable=True),
        sa.Column('check_in_at', sa.DateTime(), nullable=False),
        sa.Column('check_out_at', sa.DateTime(), nullable=True),
        sa.Column('check_in_method', sa.String(length=20), nullable=False),
        sa.Column('attendance_status', sa.String(length=30), nullable=False, server_default='VALID'),
        sa.Column('override_reason', sa.String(length=500), nullable=True),
        sa.Column('override_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_attendance_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_attendance_branch_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_attendance_member_id'),
        sa.ForeignKeyConstraint(['subscription_id'], ['member_subscriptions.id'], name='fk_attendance_subscription_id'),
        sa.ForeignKeyConstraint(['access_device_id'], ['access_devices.id'], name='fk_attendance_device_id'),
        sa.ForeignKeyConstraint(['override_by'], ['users.id'], name='fk_attendance_override_by'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attendance_member_date', 'attendance_records', ['member_id', 'check_in_at'])
    op.create_index('ix_attendance_branch_date', 'attendance_records', ['branch_id', 'check_in_at'])
    op.create_index('ix_attendance_tenant_status', 'attendance_records', ['tenant_id', 'attendance_status'])


def downgrade() -> None:
    op.drop_index('ix_attendance_tenant_status', table_name='attendance_records')
    op.drop_index('ix_attendance_branch_date', table_name='attendance_records')
    op.drop_index('ix_attendance_member_date', table_name='attendance_records')
    op.drop_table('attendance_records')
    op.drop_index('ix_access_devices_branch_status', table_name='access_devices')
    op.drop_table('access_devices')
