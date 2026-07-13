"""Shared notification payload for all channels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NotificationPayload:
    job_id: int
    job_name: str
    run_id: int
    status: str
    dry_run: bool
    trigger: str
    summary: dict[str, Any]
    duration_seconds: float | None
    error: str | None
    run_url: str

    @property
    def is_test(self) -> bool:
        return self.run_id <= 0

    def status_label(self) -> str:
        labels = {
            "success": "Success",
            "failed": "Failed",
            "partial": "Partial",
            "running": "Running",
        }
        return labels.get(self.status, self.status.title())

    def summary_lines(self) -> list[str]:
        parts: list[str] = []
        for key in (
            "matched",
            "added",
            "removed",
            "rated",
            "watched",
            "skipped",
            "errors",
            "planned",
            "unmatched_count",
        ):
            value = self.summary.get(key, 0)
            if isinstance(value, int) and value:
                parts.append(f"{key}: {value}")
        return parts or ["No changes"]

    def title(self) -> str:
        prefix = "Test: " if self.is_test else ""
        dry = " (dry run)" if self.dry_run else ""
        return f"{prefix}{self.job_name} — {self.status_label()}{dry}"

    def body_text(self) -> str:
        lines = [
            self.title(),
            f"Trigger: {self.trigger}",
        ]
        if self.duration_seconds is not None:
            lines.append(f"Duration: {self.duration_seconds:.1f}s")
        lines.extend(self.summary_lines())
        if self.error:
            lines.append(f"Error: {self.error[:500]}")
        lines.append(f"View run: {self.run_url}")
        return "\n".join(lines)
