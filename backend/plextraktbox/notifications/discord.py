"""Discord webhook notifications."""

from __future__ import annotations

import httpx

from plextraktbox.logging_setup import get_logger
from plextraktbox.models.notification_config import NotificationConfig
from plextraktbox.notifications.payload import NotificationPayload
from plextraktbox.security import decrypt_secret

log = get_logger(__name__)

_STATUS_COLORS = {
    "success": 0x57F287,
    "failed": 0xED4245,
    "partial": 0xFEE75C,
    "running": 0x5865F2,
}


async def send_discord(config: NotificationConfig, payload: NotificationPayload) -> None:
    if not config.config_enc:
        raise ValueError("Discord webhook URL is not configured")

    webhook_url = decrypt_secret(config.config_enc)
    color = _STATUS_COLORS.get(payload.status, 0x5865F2)
    fields = [
        {"name": "Status", "value": payload.status_label(), "inline": True},
        {"name": "Trigger", "value": payload.trigger, "inline": True},
    ]
    if payload.duration_seconds is not None:
        fields.append(
            {
                "name": "Duration",
                "value": f"{payload.duration_seconds:.1f}s",
                "inline": True,
            }
        )
    for line in payload.summary_lines():
        key, _, value = line.partition(": ")
        fields.append({"name": key.title(), "value": value, "inline": True})
    if payload.error:
        fields.append({"name": "Error", "value": payload.error[:1000], "inline": False})

    body = {
        "embeds": [
            {
                "title": payload.title(),
                "url": payload.run_url,
                "color": color,
                "fields": fields,
            }
        ]
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(webhook_url, json=body)
        response.raise_for_status()
    log.info("notification.discord.sent", run_id=payload.run_id, job_id=payload.job_id)
