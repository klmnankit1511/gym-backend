"""Add configurable owner portal, member profile and plan rule fields.

Revision ID: 2026_07_28_0007
Revises: 2026_07_28_0006
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_07_28_0007"
down_revision: Union[str, None] = "2026_07_28_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenant_features",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("feature_key", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_tenant_features_tenant"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], name="fk_tenant_features_user"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "feature_key", name="uq_tenant_feature"),
    )
    op.create_index("ix_tenant_features_tenant_enabled", "tenant_features", ["tenant_id", "enabled"])

    with op.batch_alter_table("members") as batch_op:
        batch_op.add_column(sa.Column("internal_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("custom_fields_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("family_group_id", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("corporate_account", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("blocked_reason", sa.String(length=500), nullable=True))

    with op.batch_alter_table("membership_plans") as batch_op:
        batch_op.add_column(sa.Column("security_deposit", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("default_discount", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("terms_and_conditions", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("rules_json", sa.JSON(), nullable=True))

    op.create_table(
        "member_timeline_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("member_id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_member_timeline_tenant"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], name="fk_member_timeline_member"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name="fk_member_timeline_user"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_member_timeline_member_date", "member_timeline_events", ["member_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_member_timeline_member_date", table_name="member_timeline_events")
    op.drop_table("member_timeline_events")
    with op.batch_alter_table("membership_plans") as batch_op:
        batch_op.drop_column("rules_json")
        batch_op.drop_column("terms_and_conditions")
        batch_op.drop_column("default_discount")
        batch_op.drop_column("security_deposit")
    with op.batch_alter_table("members") as batch_op:
        batch_op.drop_column("blocked_reason")
        batch_op.drop_column("corporate_account")
        batch_op.drop_column("family_group_id")
        batch_op.drop_column("custom_fields_json")
        batch_op.drop_column("internal_notes")
    op.drop_index("ix_tenant_features_tenant_enabled", table_name="tenant_features")
    op.drop_table("tenant_features")
