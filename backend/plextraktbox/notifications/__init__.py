"""Notification payload and channel dispatch."""

from __future__ import annotations

from plextraktbox.notifications.dispatcher import dispatch_notifications
from plextraktbox.notifications.payload import NotificationPayload

__all__ = ["NotificationPayload", "dispatch_notifications"]
