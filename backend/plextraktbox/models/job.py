"""Sync job definitions."""

from __future__ import annotations

import json
from enum import StrEnum

from sqlmodel import Field, SQLModel

from plextraktbox.sync.plans import DataType


class SourcePair(StrEnum):
    PLEX_TRAKT = "plex_trakt"
    LETTERBOXD_PLEX = "letterboxd_plex"
    LETTERBOXD_TRAKT = "letterboxd_trakt"


class NotifyMode(StrEnum):
    INHERIT = "inherit"
    CUSTOM = "custom"
    DISABLED = "disabled"


class Job(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    source_pair: SourcePair = Field(index=True)
    enabled: bool = Field(default=True)
    cron: str = Field(default="0 3 * * *")
    dry_run: bool = Field(default=False)
    require_dry_run_first: bool = Field(default=True)
    data_types_json: str = Field(default='["watchlist"]')
    notify_override_json: str = Field(default='{"mode":"inherit"}')
    exclude_ids_json: str = Field(default="{}")

    def notify_mode(self) -> NotifyMode:
        try:
            raw = json.loads(self.notify_override_json)
        except json.JSONDecodeError:
            return NotifyMode.INHERIT
        if not isinstance(raw, dict):
            return NotifyMode.INHERIT
        mode = raw.get("mode", NotifyMode.INHERIT.value)
        try:
            return NotifyMode(str(mode))
        except ValueError:
            return NotifyMode.INHERIT

    @staticmethod
    def dump_notify_mode(mode: NotifyMode) -> str:
        return json.dumps({"mode": mode.value})

    def data_types(self) -> set[DataType]:
        try:
            raw = json.loads(self.data_types_json)
        except json.JSONDecodeError:
            return set()
        if not isinstance(raw, list):
            return set()
        result: set[DataType] = set()
        for item in raw:
            try:
                result.add(DataType(str(item)))
            except ValueError:
                continue
        return result

    def services_for_pair(self) -> set[str]:
        if self.source_pair == SourcePair.PLEX_TRAKT:
            return {"plex", "trakt"}
        if self.source_pair == SourcePair.LETTERBOXD_PLEX:
            return {"letterboxd", "plex"}
        if self.source_pair == SourcePair.LETTERBOXD_TRAKT:
            return {"letterboxd", "trakt"}
        return set()

    def validate_data_types(self) -> list[str]:
        errors: list[str] = []
        services = self.services_for_pair()
        for data_type in self.data_types():
            if data_type == DataType.WATCHLIST and self.source_pair != SourcePair.PLEX_TRAKT:
                errors.append("watchlist requires a plex_trakt job")
            if data_type == DataType.RATINGS and "letterboxd" not in services:
                errors.append("ratings requires letterboxd in the source pair")
            if data_type == DataType.WATCHED and "trakt" not in services:
                errors.append("watched requires trakt in the source pair")
        return errors

    @staticmethod
    def dump_data_types(data_types: set[DataType]) -> str:
        return json.dumps(sorted(dt.value for dt in data_types))

    def exclude_ids(self) -> dict[str, set[str]]:
        from plextraktbox.sync.excludes import normalize_exclude_ids

        try:
            raw = json.loads(self.exclude_ids_json)
        except json.JSONDecodeError:
            return normalize_exclude_ids({})
        return normalize_exclude_ids(raw)

    @staticmethod
    def dump_exclude_ids(exclude_ids: dict[str, list[str]] | dict[str, set[str]]) -> str:
        from plextraktbox.sync.excludes import dump_exclude_ids, normalize_exclude_ids

        return json.dumps(dump_exclude_ids(normalize_exclude_ids(exclude_ids)))
