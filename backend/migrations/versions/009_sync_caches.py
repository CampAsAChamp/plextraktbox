"""Add Phase 21 sync cache tables.

Revision ID: 009_sync_caches
Revises: 008_settings_and_job_safety
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009_sync_caches"
down_revision: str | None = "008_settings_and_job_safety"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _table_exists("letterboxd_slug_cache"):
        op.create_table(
            "letterboxd_slug_cache",
            sa.Column("slug", sa.String(length=256), nullable=False),
            sa.Column("tmdb", sa.String(length=64), nullable=True),
            sa.Column("imdb", sa.String(length=64), nullable=True),
            sa.Column("title", sa.String(length=512), nullable=True),
            sa.Column("year", sa.String(length=16), nullable=True),
            sa.Column("resolved_at", sa.DateTime(), nullable=True),
            sa.Column("miss_until", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("slug"),
        )

    if not _table_exists("trakt_list_cache"):
        op.create_table(
            "trakt_list_cache",
            sa.Column("list_kind", sa.String(length=32), nullable=False),
            sa.Column("account_key", sa.String(length=128), nullable=False),
            sa.Column("items_json", sa.String(), nullable=False),
            sa.Column("fetched_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("list_kind", "account_key"),
        )

    if not _table_exists("plex_discover_key_cache"):
        op.create_table(
            "plex_discover_key_cache",
            sa.Column("id_provider", sa.String(length=16), nullable=False),
            sa.Column("external_id", sa.String(length=64), nullable=False),
            sa.Column("libtype", sa.String(length=16), nullable=False),
            sa.Column("discover_key", sa.String(length=128), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id_provider", "external_id", "libtype"),
        )


def downgrade() -> None:
    if _table_exists("plex_discover_key_cache"):
        op.drop_table("plex_discover_key_cache")
    if _table_exists("trakt_list_cache"):
        op.drop_table("trakt_list_cache")
    if _table_exists("letterboxd_slug_cache"):
        op.drop_table("letterboxd_slug_cache")
