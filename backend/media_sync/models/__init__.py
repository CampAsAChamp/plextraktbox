"""SQLModel table definitions.

Models are imported here so ``SQLModel.metadata`` is fully populated whenever the
package is imported (used by ``db.init_db`` and Alembic autogenerate).

Tables are added incrementally per build phase.
"""

from __future__ import annotations

# Phase 1+ models are imported here as they are added, e.g.:
# from media_sync.models.user import User  # noqa: F401

__all__: list[str] = []
