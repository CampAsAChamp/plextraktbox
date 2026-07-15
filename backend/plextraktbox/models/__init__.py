"""SQLModel table definitions.

Models are imported here so ``SQLModel.metadata`` is fully populated whenever the
package is imported (used by ``db.init_db`` and Alembic autogenerate).

Tables are added incrementally per build phase.
"""

from __future__ import annotations

from plextraktbox.models.connection import Connection  # noqa: F401
from plextraktbox.models.inapp_notification import InAppNotification  # noqa: F401
from plextraktbox.models.job import Job  # noqa: F401
from plextraktbox.models.job_run import JobRun  # noqa: F401
from plextraktbox.models.log_entry import LogEntry  # noqa: F401
from plextraktbox.models.notification_config import NotificationConfig  # noqa: F401
from plextraktbox.models.setting import Setting  # noqa: F401
from plextraktbox.models.user import User  # noqa: F401

__all__ = [
    "Connection",
    "InAppNotification",
    "Job",
    "JobRun",
    "LogEntry",
    "NotificationConfig",
    "Setting",
    "User",
]
