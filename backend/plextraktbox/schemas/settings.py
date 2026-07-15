"""Settings API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from plextraktbox.cron import (
    validate_cron_expression,
    validate_cron_timezone,
    validate_iana_timezone,
)
from plextraktbox.services.settings import AppSettings
from plextraktbox.sync.excludes import EXCLUDE_ID_KEYS, dump_exclude_ids, normalize_exclude_ids


class ExcludeIds(BaseModel):
    tmdb: list[str] = Field(default_factory=list)
    imdb: list[str] = Field(default_factory=list)
    tvdb: list[str] = Field(default_factory=list)

    @field_validator("tmdb", "imdb", "tvdb", mode="before")
    @classmethod
    def _coerce_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("exclude id provider values must be a list")
        return [str(item).strip() for item in value if str(item).strip()]


class SettingsResponse(BaseModel):
    default_cron: str
    cron_timezone: str
    cron_timezone_resolved: str
    log_retention_days: int
    global_dry_run: bool
    exclude_ids: ExcludeIds
    ui_theme: str

    @classmethod
    def from_app_settings(cls, settings: AppSettings) -> SettingsResponse:
        normalized = dump_exclude_ids(normalize_exclude_ids(settings.exclude_ids))
        return cls(
            default_cron=settings.default_cron,
            cron_timezone=settings.cron_timezone,
            cron_timezone_resolved=settings.cron_timezone_resolved,
            log_retention_days=settings.log_retention_days,
            global_dry_run=settings.global_dry_run,
            exclude_ids=ExcludeIds(
                tmdb=normalized.get("tmdb", []),
                imdb=normalized.get("imdb", []),
                tvdb=normalized.get("tvdb", []),
            ),
            ui_theme=settings.ui_theme,
        )


class SettingsUpdateRequest(BaseModel):
    default_cron: str
    cron_timezone: str = "UTC"
    cron_local_zone: str | None = None
    log_retention_days: int = Field(ge=1, le=3650)
    global_dry_run: bool
    exclude_ids: ExcludeIds = Field(default_factory=ExcludeIds)

    @field_validator("default_cron")
    @classmethod
    def validate_cron(cls, value: str) -> str:
        return validate_cron_expression(value)

    @field_validator("cron_timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        return validate_cron_timezone(value)

    @field_validator("cron_local_zone")
    @classmethod
    def validate_local_zone(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return validate_iana_timezone(value)

    def to_app_settings(self) -> AppSettings:
        raw = {key: getattr(self.exclude_ids, key) for key in EXCLUDE_ID_KEYS}
        return AppSettings(
            default_cron=self.default_cron,
            cron_timezone=self.cron_timezone,
            cron_local_zone=self.cron_local_zone,
            log_retention_days=self.log_retention_days,
            global_dry_run=self.global_dry_run,
            exclude_ids=dump_exclude_ids(normalize_exclude_ids(raw)),
        )
