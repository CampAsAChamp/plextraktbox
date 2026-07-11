"""Remove email notification configs."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "007_remove_email_notifications"
down_revision: str | None = "006_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DELETE FROM notificationconfig WHERE channel = 'email'")


def downgrade() -> None:
    pass
