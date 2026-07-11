"""Add connection table."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_connection"
down_revision: str | None = "001_user"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "connection",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("config_json", sa.String(), nullable=False),
        sa.Column("secret_enc", sa.String(), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("connection", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_connection_service"), ["service"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("connection", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_connection_service"))
    op.drop_table("connection")
