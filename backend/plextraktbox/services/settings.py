"""Typed accessors for the ``setting`` key/value table."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from sqlmodel import Session, select

from plextraktbox.cron import (
    DEFAULT_CRON_TIMEZONE,
    resolve_cron_timezone,
    validate_cron_expression,
    validate_cron_timezone,
    validate_iana_timezone,
)
from plextraktbox.models.setting import Setting
from plextraktbox.sync.excludes import dump_exclude_ids, normalize_exclude_ids

KEY_DEFAULT_CRON = "default_cron"
KEY_CRON_TIMEZONE = "cron_timezone"
KEY_CRON_LOCAL_ZONE = "cron_local_zone"
KEY_LOG_RETENTION_DAYS = "log_retention_days"
KEY_GLOBAL_DRY_RUN = "global_dry_run"
KEY_EXCLUDE_IDS = "exclude_ids"

DEFAULT_CRON = "0 3 * * *"
DEFAULT_LOG_RETENTION_DAYS = 30
DEFAULT_GLOBAL_DRY_RUN = True


@dataclass
class AppSettings:
    default_cron: str = DEFAULT_CRON
    cron_timezone: str = DEFAULT_CRON_TIMEZONE
    cron_local_zone: str | None = None
    log_retention_days: int = DEFAULT_LOG_RETENTION_DAYS
    global_dry_run: bool = DEFAULT_GLOBAL_DRY_RUN
    exclude_ids: dict[str, list[str]] = field(default_factory=dict)

    @property
    def cron_timezone_resolved(self) -> str:
        return resolve_cron_timezone(self.cron_timezone, local_zone=self.cron_local_zone)


def _read_json(session: Session, key: str) -> object | None:
    row = session.get(Setting, key)
    if row is None:
        return None
    try:
        return json.loads(row.value_json)
    except json.JSONDecodeError:
        return None


def _write_json(session: Session, key: str, value: object) -> None:
    row = session.get(Setting, key)
    payload = json.dumps(value)
    if row is None:
        session.add(Setting(key=key, value_json=payload))
    else:
        row.value_json = payload
        session.add(row)


def ensure_defaults(session: Session) -> AppSettings:
    """Persist missing keys with defaults and return the current settings."""
    changed = False
    if _read_json(session, KEY_DEFAULT_CRON) is None:
        _write_json(session, KEY_DEFAULT_CRON, DEFAULT_CRON)
        changed = True
    if _read_json(session, KEY_CRON_TIMEZONE) is None:
        _write_json(session, KEY_CRON_TIMEZONE, DEFAULT_CRON_TIMEZONE)
        changed = True
    if _read_json(session, KEY_LOG_RETENTION_DAYS) is None:
        _write_json(session, KEY_LOG_RETENTION_DAYS, DEFAULT_LOG_RETENTION_DAYS)
        changed = True
    if _read_json(session, KEY_GLOBAL_DRY_RUN) is None:
        _write_json(session, KEY_GLOBAL_DRY_RUN, DEFAULT_GLOBAL_DRY_RUN)
        changed = True
    if _read_json(session, KEY_EXCLUDE_IDS) is None:
        _write_json(session, KEY_EXCLUDE_IDS, {})
        changed = True
    if changed:
        session.commit()
    return get_app_settings(session)


def get_app_settings(session: Session) -> AppSettings:
    cron_raw = _read_json(session, KEY_DEFAULT_CRON)
    default_cron = DEFAULT_CRON
    if isinstance(cron_raw, str) and cron_raw.strip():
        try:
            default_cron = validate_cron_expression(cron_raw)
        except ValueError:
            default_cron = DEFAULT_CRON

    tz_raw = _read_json(session, KEY_CRON_TIMEZONE)
    cron_timezone = DEFAULT_CRON_TIMEZONE
    if isinstance(tz_raw, str) and tz_raw.strip():
        try:
            cron_timezone = validate_cron_timezone(tz_raw)
        except ValueError:
            cron_timezone = DEFAULT_CRON_TIMEZONE

    local_raw = _read_json(session, KEY_CRON_LOCAL_ZONE)
    cron_local_zone: str | None = None
    if isinstance(local_raw, str) and local_raw.strip():
        try:
            cron_local_zone = validate_iana_timezone(local_raw)
        except ValueError:
            cron_local_zone = None

    retention_raw = _read_json(session, KEY_LOG_RETENTION_DAYS)
    log_retention_days = DEFAULT_LOG_RETENTION_DAYS
    if isinstance(retention_raw, int) and retention_raw >= 1:
        log_retention_days = retention_raw
    elif isinstance(retention_raw, float) and retention_raw >= 1:
        log_retention_days = int(retention_raw)

    dry_raw = _read_json(session, KEY_GLOBAL_DRY_RUN)
    global_dry_run = DEFAULT_GLOBAL_DRY_RUN if not isinstance(dry_raw, bool) else dry_raw

    exclude_raw = _read_json(session, KEY_EXCLUDE_IDS)
    exclude_ids = dump_exclude_ids(normalize_exclude_ids(exclude_raw if exclude_raw is not None else {}))

    return AppSettings(
        default_cron=default_cron,
        cron_timezone=cron_timezone,
        cron_local_zone=cron_local_zone,
        log_retention_days=log_retention_days,
        global_dry_run=global_dry_run,
        exclude_ids=exclude_ids,
    )


def update_app_settings(session: Session, settings: AppSettings) -> AppSettings:
    validate_cron_expression(settings.default_cron)
    cron_timezone = validate_cron_timezone(settings.cron_timezone)
    cron_local_zone: str | None = None
    if settings.cron_local_zone is not None and settings.cron_local_zone.strip():
        cron_local_zone = validate_iana_timezone(settings.cron_local_zone)
    if cron_timezone == "local" and cron_local_zone is None:
        # Keep any previously saved device zone when the client omits it.
        previous = get_app_settings(session).cron_local_zone
        cron_local_zone = previous
    if settings.log_retention_days < 1:
        raise ValueError("log_retention_days must be at least 1")
    exclude_ids = dump_exclude_ids(normalize_exclude_ids(settings.exclude_ids))

    _write_json(session, KEY_DEFAULT_CRON, settings.default_cron)
    _write_json(session, KEY_CRON_TIMEZONE, cron_timezone)
    if cron_local_zone is not None:
        _write_json(session, KEY_CRON_LOCAL_ZONE, cron_local_zone)
    _write_json(session, KEY_LOG_RETENTION_DAYS, settings.log_retention_days)
    _write_json(session, KEY_GLOBAL_DRY_RUN, settings.global_dry_run)
    _write_json(session, KEY_EXCLUDE_IDS, exclude_ids)
    session.commit()
    return get_app_settings(session)


def list_all_setting_rows(session: Session) -> list[Setting]:
    return list(session.exec(select(Setting).order_by(Setting.key)).all())  # type: ignore[arg-type]
