"""Add user table."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_user"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_email"), ["email"], unique=True)
        batch_op.create_index(batch_op.f("ix_user_username"), ["username"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_username"))
        batch_op.drop_index(batch_op.f("ix_user_email"))
    op.drop_table("user")
