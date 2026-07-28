"""Create gym core tables - members, staff, trainers

Revision ID: 2026_07_28_0002
Revises: 2026_07_25_0001
Create Date: 2026-07-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_07_28_0002"
down_revision: Union[str, None] = "2026_07_25_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create staff table
    op.create_table(
        'staff',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('employee_code', sa.String(length=50), nullable=False),
        sa.Column('designation', sa.String(length=100), nullable=True),
        sa.Column('joining_date', sa.Date(), nullable=True),
        sa.Column('employment_type', sa.String(length=20), nullable=True),
        sa.Column('monthly_salary', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('commission_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_staff_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_staff_branch_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_staff_user_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'employee_code', name='uq_staff_tenant_employee_code'),
        sa.UniqueConstraint('user_id', name='uq_staff_user_id')
    )
    op.create_index('ix_staff_branch_status', 'staff', ['branch_id', 'status'])

    # Create trainers table
    op.create_table(
        'trainers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('trainer_code', sa.String(length=50), nullable=False),
        sa.Column('specialization', sa.String(length=255), nullable=True),
        sa.Column('experience_years', sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('hourly_rate', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('commission_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_trainers_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_trainers_branch_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_trainers_user_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'trainer_code', name='uq_trainers_tenant_code'),
        sa.UniqueConstraint('user_id', name='uq_trainers_user_id')
    )
    op.create_index('ix_trainers_branch_status', 'trainers', ['branch_id', 'status'])

    # Create trainer_availability table
    op.create_table(
        'trainer_availability',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('trainer_id', sa.String(length=36), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id'], name='fk_trainer_availability_trainer_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trainer_id', 'day_of_week', 'start_time', 'end_time', name='uq_trainer_availability_slot')
    )

    # Create members table
    op.create_table(
        'members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('home_branch_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('assigned_trainer_id', sa.String(length=36), nullable=True),
        sa.Column('member_code', sa.String(length=50), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=150), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=False),
        sa.Column('alternate_phone', sa.String(length=30), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('blood_group', sa.String(length=10), nullable=True),
        sa.Column('address_line1', sa.String(length=200), nullable=True),
        sa.Column('address_line2', sa.String(length=200), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('emergency_contact_name', sa.String(length=150), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(length=30), nullable=True),
        sa.Column('occupation', sa.String(length=100), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('joining_date', sa.Date(), nullable=False),
        sa.Column('profile_photo_url', sa.String(length=500), nullable=True),
        sa.Column('medical_notes', sa.Text(), nullable=True),
        sa.Column('fitness_goal', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_members_tenant_id'),
        sa.ForeignKeyConstraint(['home_branch_id'], ['branches.id'], name='fk_members_branch_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_members_user_id'),
        sa.ForeignKeyConstraint(['assigned_trainer_id'], ['trainers.id'], name='fk_members_trainer_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'member_code', name='uq_members_tenant_code'),
        sa.UniqueConstraint('user_id', name='uq_members_user_id')
    )
    op.create_index('ix_members_tenant_phone', 'members', ['tenant_id', 'phone'])
    op.create_index('ix_members_branch_status', 'members', ['home_branch_id', 'status'])
    op.create_index('ix_members_trainer', 'members', ['assigned_trainer_id'])

    # Create member_documents table
    op.create_table(
        'member_documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('uploaded_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_member_documents_tenant_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_member_documents_member_id'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], name='fk_member_documents_uploaded_by'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_member_documents_member_type', 'member_documents', ['member_id', 'document_type'])

    # Create member_consents table
    op.create_table(
        'member_consents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('consent_type', sa.String(length=50), nullable=False),
        sa.Column('document_version', sa.String(length=50), nullable=False),
        sa.Column('accepted', sa.Boolean(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_member_consents_tenant_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_member_consents_member_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_member_consents_member_type', 'member_consents', ['member_id', 'consent_type'])


def downgrade() -> None:
    op.drop_index('ix_member_consents_member_type', table_name='member_consents')
    op.drop_table('member_consents')
    op.drop_index('ix_member_documents_member_type', table_name='member_documents')
    op.drop_table('member_documents')
    op.drop_index('ix_members_trainer', table_name='members')
    op.drop_index('ix_members_branch_status', table_name='members')
    op.drop_index('ix_members_tenant_phone', table_name='members')
    op.drop_table('members')
    op.drop_table('trainer_availability')
    op.drop_index('ix_trainers_branch_status', table_name='trainers')
    op.drop_table('trainers')
    op.drop_index('ix_staff_branch_status', table_name='staff')
    op.drop_table('staff')
