"""SQLModel table definitions.

Models are imported here so ``SQLModel.metadata`` is fully populated whenever the
package is imported (used by ``db.init_db`` and Alembic autogenerate).

Tables are added incrementally per build phase.
"""

from __future__ import annotations

from plextraktbox.models.connection import Connection  # noqa: F401
from plextraktbox.models.job import Job  # noqa: F401
from plextraktbox.models.job_run import JobRun  # noqa: F401
from plextraktbox.models.user import User  # noqa: F401

__all__ = ["Connection", "Job", "JobRun", "User"]
