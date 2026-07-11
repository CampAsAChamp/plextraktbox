"""Add notification_config, inapp_notification, and job notify override."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_notifications"
down_revision: str | None = "005_log_entry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notificationconfig",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("on_success", sa.Boolean(), nullable=False),
        sa.Column("on_failure", sa.Boolean(), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("config_enc", sa.String(), nullable=False),
        sa.Column("config_json", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("notificationconfig", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_notificationconfig_channel"), ["channel"], unique=False)
        batch_op.create_index(batch_op.f("ix_notificationconfig_scope"), ["scope"], unique=False)
        batch_op.create_index(batch_op.f("ix_notificationconfig_job_id"), ["job_id"], unique=False)

    op.create_table(
        "inappnotification",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("inappnotification", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_inappnotification_created_at"), ["created_at"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_inappnotification_read"), ["read"], unique=False)
        batch_op.create_index(batch_op.f("ix_inappnotification_run_id"), ["run_id"], unique=False)

    with op.batch_alter_table("job", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("notify_override_json", sa.String(), nullable=False, server_default='{"mode":"inherit"}')
        )


def downgrade() -> None:
    with op.batch_alter_table("job", schema=None) as batch_op:
        batch_op.drop_column("notify_override_json")

    with op.batch_alter_table("inappnotification", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_inappnotification_run_id"))
        batch_op.drop_index(batch_op.f("ix_inappnotification_read"))
        batch_op.drop_index(batch_op.f("ix_inappnotification_created_at"))
    op.drop_table("inappnotification")

    with op.batch_alter_table("notificationconfig", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_notificationconfig_job_id"))
        batch_op.drop_index(batch_op.f("ix_notificationconfig_scope"))
        batch_op.drop_index(batch_op.f("ix_notificationconfig_channel"))
    op.drop_table("notificationconfig")
