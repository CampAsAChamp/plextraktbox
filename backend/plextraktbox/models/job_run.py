"""Recorded sync job executions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlmodel import Field, SQLModel

from plextraktbox.sync.plans import RunSummary


def _parse_identifiers(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for key in ("tmdb", "imdb", "tvdb"):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            out[key] = value.strip()
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            out[key] = str(int(value)) if float(value).is_integer() else str(value)
    return out


class RunTrigger(StrEnum):
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class JobRunStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class JobRun(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(index=True)
    job_name: str | None = Field(default=None, nullable=True)
    trigger: RunTrigger = Field(default=RunTrigger.MANUAL)
    dry_run: bool = Field(default=False)
    status: JobRunStatus = Field(default=JobRunStatus.RUNNING, index=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = Field(default=None, nullable=True)
    summary_json: str = Field(default="{}")
    error: str | None = Field(default=None, nullable=True)

    def summary(self) -> RunSummary:
        try:
            raw: dict[str, Any] = json.loads(self.summary_json)
        except json.JSONDecodeError:
            return RunSummary()

        from plextraktbox.sync.plans import UnmatchedItem

        unmatched_raw = raw.get("unmatched") or []
        unmatched: list[UnmatchedItem] = []
        if isinstance(unmatched_raw, list):
            for entry in unmatched_raw:
                if not isinstance(entry, dict):
                    continue
                unmatched.append(
                    UnmatchedItem(
                        source=str(entry.get("source", "")),
                        data_type=str(entry.get("data_type", "")),
                        title=str(entry.get("title", "")),
                        source_key=str(entry.get("source_key", "")),
                        reason=str(entry.get("reason", "")),
                        identifiers=_parse_identifiers(entry.get("identifiers")),
                    )
                )

        return RunSummary(
            matched=int(raw.get("matched", 0)),
            added=int(raw.get("added", 0)),
            removed=int(raw.get("removed", 0)),
            rated=int(raw.get("rated", 0)),
            watched=int(raw.get("watched", 0)),
            skipped=int(raw.get("skipped", 0)),
            errors=int(raw.get("errors", 0)),
            planned=int(raw.get("planned", 0)),
            shows_added=int(raw.get("shows_added", 0)),
            shows_removed=int(raw.get("shows_removed", 0)),
            episodes_watched=int(raw.get("episodes_watched", 0)),
            unmatched=unmatched,
        )

    def set_summary(self, summary: RunSummary) -> None:
        self.summary_json = json.dumps(summary.to_dict())
