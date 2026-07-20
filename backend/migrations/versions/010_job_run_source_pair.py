"""Persist source_pair on job runs for history after job deletion."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010_job_run_source_pair"
down_revision: str | None = "009_sync_caches"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("jobrun", schema=None) as batch_op:
        batch_op.add_column(sa.Column("source_pair", sa.String(length=32), nullable=True))

    op.execute(
        """
        UPDATE jobrun
        SET source_pair = (
            SELECT job.source_pair
            FROM job
            WHERE job.id = jobrun.job_id
        )
        WHERE source_pair IS NULL
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("jobrun", schema=None) as batch_op:
        batch_op.drop_column("source_pair")
