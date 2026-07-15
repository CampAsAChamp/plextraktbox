"""Add setting table and job safety columns.

Idempotent for local DBs where ``init_db()`` / ``SQLModel.metadata.create_all``
may have already created the ``setting`` table before Alembic ran this revision.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_settings_and_job_safety"
down_revision: str | None = "007_remove_email_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return name in inspector.get_table_names()


def _column_names(table: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    if not _table_exists("setting"):
        op.create_table(
            "setting",
            sa.Column("key", sa.String(length=64), nullable=False),
            sa.Column("value_json", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("key"),
        )

    job_columns = _column_names("job")
    with op.batch_alter_table("job", schema=None) as batch_op:
        if "require_dry_run_first" not in job_columns:
            batch_op.add_column(
                sa.Column(
                    "require_dry_run_first",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.true(),
                )
            )
        if "exclude_ids_json" not in job_columns:
            batch_op.add_column(
                sa.Column(
                    "exclude_ids_json",
                    sa.String(),
                    nullable=False,
                    server_default="{}",
                )
            )


def downgrade() -> None:
    job_columns = _column_names("job")
    with op.batch_alter_table("job", schema=None) as batch_op:
        if "exclude_ids_json" in job_columns:
            batch_op.drop_column("exclude_ids_json")
        if "require_dry_run_first" in job_columns:
            batch_op.drop_column("require_dry_run_first")
    if _table_exists("setting"):
        op.drop_table("setting")
