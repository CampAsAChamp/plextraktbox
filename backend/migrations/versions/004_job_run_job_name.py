"""Persist job name on job runs for history after job deletion."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_job_run_job_name"
down_revision: str | None = "003_job"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("jobrun", schema=None) as batch_op:
        batch_op.add_column(sa.Column("job_name", sa.String(), nullable=True))

    op.execute(
        """
        UPDATE jobrun
        SET job_name = (
            SELECT job.name
            FROM job
            WHERE job.id = jobrun.job_id
        )
        WHERE job_name IS NULL
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("jobrun", schema=None) as batch_op:
        batch_op.drop_column("job_name")
