"""Add log_entry table for persisted run logs."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_log_entry"
down_revision: str | None = "004_job_run_job_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "logentry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("ts", sa.DateTime(), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("logger", sa.String(length=255), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("context_json", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("logentry", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_logentry_run_id"), ["run_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_logentry_ts"), ["ts"], unique=False)
        batch_op.create_index("ix_logentry_run_id_id", ["run_id", "id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("logentry", schema=None) as batch_op:
        batch_op.drop_index("ix_logentry_run_id_id")
        batch_op.drop_index(batch_op.f("ix_logentry_ts"))
        batch_op.drop_index(batch_op.f("ix_logentry_run_id"))
    op.drop_table("logentry")
