"""Create classes, workouts, and training tables

Revision ID: 2026_07_28_0005
Revises: 2026_07_28_0004
Create Date: 2026-07-28 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_07_28_0005"
down_revision: Union[str, None] = "2026_07_28_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create class_types table
    op.create_table(
        'class_types',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_duration_min', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_class_types_tenant_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_class_types_tenant_name')
    )

    # Create class_schedules table
    op.create_table(
        'class_schedules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('class_type_id', sa.String(length=36), nullable=False),
        sa.Column('trainer_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('room_name', sa.String(length=100), nullable=True),
        sa.Column('start_at', sa.DateTime(), nullable=False),
        sa.Column('end_at', sa.DateTime(), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('waiting_list_limit', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('booking_opens_at', sa.DateTime(), nullable=True),
        sa.Column('booking_closes_at', sa.DateTime(), nullable=True),
        sa.Column('cancellation_cutoff_min', sa.Integer(), nullable=True),
        sa.Column('recurrence_group_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='SCHEDULED'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_class_schedules_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_class_schedules_branch_id'),
        sa.ForeignKeyConstraint(['class_type_id'], ['class_types.id'], name='fk_class_schedules_type_id'),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id'], name='fk_class_schedules_trainer_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_class_schedules_branch_start', 'class_schedules', ['branch_id', 'start_at'])
    op.create_index('ix_class_schedules_trainer_start', 'class_schedules', ['trainer_id', 'start_at'])

    # Create class_bookings table
    op.create_table(
        'class_bookings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('class_schedule_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('subscription_id', sa.String(length=36), nullable=True),
        sa.Column('booking_status', sa.String(length=20), nullable=False, server_default='BOOKED'),
        sa.Column('waiting_position', sa.Integer(), nullable=True),
        sa.Column('booked_at', sa.DateTime(), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancellation_reason', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_class_bookings_tenant_id'),
        sa.ForeignKeyConstraint(['class_schedule_id'], ['class_schedules.id'], name='fk_class_bookings_schedule_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_class_bookings_member_id'),
        sa.ForeignKeyConstraint(['subscription_id'], ['member_subscriptions.id'], name='fk_class_bookings_subscription_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('class_schedule_id', 'member_id', name='uq_class_bookings_schedule_member')
    )
    op.create_index('ix_class_bookings_member_status', 'class_bookings', ['member_id', 'booking_status'])
    op.create_index('ix_class_bookings_schedule_status', 'class_bookings', ['class_schedule_id', 'booking_status'])

    # Create exercises table
    op.create_table(
        'exercises',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('muscle_group', sa.String(length=100), nullable=True),
        sa.Column('equipment', sa.String(length=100), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('video_url', sa.String(length=500), nullable=True),
        sa.Column('is_global', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_exercises_tenant_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_exercises_tenant_name', 'exercises', ['tenant_id', 'name'])

    # Create workout_templates table
    op.create_table(
        'workout_templates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('created_by_trainer_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('difficulty_level', sa.String(length=20), nullable=True),
        sa.Column('goal_type', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_workout_templates_tenant_id'),
        sa.ForeignKeyConstraint(['created_by_trainer_id'], ['trainers.id'], name='fk_workout_templates_trainer_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workout_templates_tenant_status', 'workout_templates', ['tenant_id', 'status'])

    # Create workout_template_exercises table
    op.create_table(
        'workout_template_exercises',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workout_template_id', sa.String(length=36), nullable=False),
        sa.Column('exercise_id', sa.String(length=36), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('target_sets', sa.Integer(), nullable=True),
        sa.Column('target_reps', sa.String(length=50), nullable=True),
        sa.Column('target_weight', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('rest_seconds', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['workout_template_id'], ['workout_templates.id'], name='fk_workout_template_exercises_template_id'),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], name='fk_workout_template_exercises_exercise_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workout_template_id', 'day_number', 'sequence_number', name='uq_workout_template_sequence')
    )

    # Create member_workout_plans table
    op.create_table(
        'member_workout_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('trainer_id', sa.String(length=36), nullable=True),
        sa.Column('workout_template_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_member_workout_plans_tenant_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_member_workout_plans_member_id'),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id'], name='fk_member_workout_plans_trainer_id'),
        sa.ForeignKeyConstraint(['workout_template_id'], ['workout_templates.id'], name='fk_member_workout_plans_template_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_member_workout_plans_member_status', 'member_workout_plans', ['member_id', 'status'])

    # Create workout_sessions table
    op.create_table(
        'workout_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('workout_plan_id', sa.String(length=36), nullable=True),
        sa.Column('trainer_id', sa.String(length=36), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='STARTED'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_workout_sessions_tenant_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_workout_sessions_member_id'),
        sa.ForeignKeyConstraint(['workout_plan_id'], ['member_workout_plans.id'], name='fk_workout_sessions_plan_id'),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id'], name='fk_workout_sessions_trainer_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workout_sessions_member_date', 'workout_sessions', ['member_id', 'started_at'])

    # Create workout_session_exercises table
    op.create_table(
        'workout_session_exercises',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workout_session_id', sa.String(length=36), nullable=False),
        sa.Column('exercise_id', sa.String(length=36), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('sets_completed', sa.Integer(), nullable=True),
        sa.Column('reps_completed', sa.String(length=100), nullable=True),
        sa.Column('weight_used', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('distance_km', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('calories_burned', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['workout_session_id'], ['workout_sessions.id'], name='fk_workout_session_exercises_session_id'),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], name='fk_workout_session_exercises_exercise_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workout_session_id', 'sequence_number', name='uq_workout_session_sequence')
    )

    # Create body_measurements table
    op.create_table(
        'body_measurements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('measured_by', sa.String(length=36), nullable=True),
        sa.Column('measurement_date', sa.Date(), nullable=False),
        sa.Column('weight_kg', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('height_cm', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('bmi', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('body_fat_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('muscle_mass_kg', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('chest_cm', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('waist_cm', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('hips_cm', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('arm_cm', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('thigh_cm', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_body_measurements_tenant_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_body_measurements_member_id'),
        sa.ForeignKeyConstraint(['measured_by'], ['users.id'], name='fk_body_measurements_measured_by'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_body_measurements_member_date', 'body_measurements', ['member_id', 'measurement_date'])

    # Create progress_photos table
    op.create_table(
        'progress_photos',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('photo_date', sa.Date(), nullable=False),
        sa.Column('photo_type', sa.String(length=20), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_progress_photos_tenant_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_progress_photos_member_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_progress_photos_member_date', 'progress_photos', ['member_id', 'photo_date'])

    # Create personal_training_sessions table
    op.create_table(
        'personal_training_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('trainer_id', sa.String(length=36), nullable=False),
        sa.Column('subscription_id', sa.String(length=36), nullable=True),
        sa.Column('scheduled_start_at', sa.DateTime(), nullable=False),
        sa.Column('scheduled_end_at', sa.DateTime(), nullable=False),
        sa.Column('actual_start_at', sa.DateTime(), nullable=True),
        sa.Column('actual_end_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='SCHEDULED'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_pt_sessions_tenant_id'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_pt_sessions_branch_id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_pt_sessions_member_id'),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id'], name='fk_pt_sessions_trainer_id'),
        sa.ForeignKeyConstraint(['subscription_id'], ['member_subscriptions.id'], name='fk_pt_sessions_subscription_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pt_sessions_trainer_date', 'personal_training_sessions', ['trainer_id', 'scheduled_start_at'])
    op.create_index('ix_pt_sessions_member_date', 'personal_training_sessions', ['member_id', 'scheduled_start_at'])


def downgrade() -> None:
    op.drop_index('ix_pt_sessions_member_date', table_name='personal_training_sessions')
    op.drop_index('ix_pt_sessions_trainer_date', table_name='personal_training_sessions')
    op.drop_table('personal_training_sessions')
    op.drop_index('ix_progress_photos_member_date', table_name='progress_photos')
    op.drop_table('progress_photos')
    op.drop_index('ix_body_measurements_member_date', table_name='body_measurements')
    op.drop_table('body_measurements')
    op.drop_index('ix_workout_sessions_member_date', table_name='workout_sessions')
    op.drop_table('workout_session_exercises')
    op.drop_table('workout_sessions')
    op.drop_index('ix_member_workout_plans_member_status', table_name='member_workout_plans')
    op.drop_table('member_workout_plans')
    op.drop_table('workout_template_exercises')
    op.drop_index('ix_workout_templates_tenant_status', table_name='workout_templates')
    op.drop_table('workout_templates')
    op.drop_index('ix_exercises_tenant_name', table_name='exercises')
    op.drop_table('exercises')
    op.drop_index('ix_class_bookings_schedule_status', table_name='class_bookings')
    op.drop_index('ix_class_bookings_member_status', table_name='class_bookings')
    op.drop_table('class_bookings')
    op.drop_index('ix_class_schedules_trainer_start', table_name='class_schedules')
    op.drop_index('ix_class_schedules_branch_start', table_name='class_schedules')
    op.drop_table('class_schedules')
    op.drop_table('class_types')
