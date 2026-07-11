"""Apply Alembic migrations for job and job_run tables."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_job"
down_revision: str | None = "002_connection"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("source_pair", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("cron", sa.String(), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("data_types_json", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("job", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_job_source_pair"), ["source_pair"], unique=False)

    op.create_table(
        "jobrun",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("trigger", sa.String(length=16), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("summary_json", sa.String(), nullable=False),
        sa.Column("error", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("jobrun", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_jobrun_job_id"), ["job_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_jobrun_status"), ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("jobrun", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_jobrun_status"))
        batch_op.drop_index(batch_op.f("ix_jobrun_job_id"))
    op.drop_table("jobrun")

    with op.batch_alter_table("job", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_job_source_pair"))
    op.drop_table("job")
