"""App settings service tests."""

from __future__ import annotations

from sqlmodel import Session

from plextraktbox.services.settings import (
    AppSettings,
    ensure_defaults,
    get_app_settings,
    update_app_settings,
)


def test_ensure_defaults_seeds_keys(session: Session) -> None:
    settings = ensure_defaults(session)
    assert settings.default_cron == "0 3 * * *"
    assert settings.cron_timezone == "UTC"
    assert settings.cron_timezone_resolved == "UTC"
    assert settings.log_retention_days == 30
    assert settings.global_dry_run is True
    assert settings.exclude_ids == {}


def test_update_and_get_round_trip(session: Session) -> None:
    ensure_defaults(session)
    updated = update_app_settings(
        session,
        AppSettings(
            default_cron="0 4 * * *",
            cron_timezone="America/Chicago",
            log_retention_days=14,
            global_dry_run=False,
            exclude_ids={"tmdb": ["42"], "imdb": ["tt1"]},
        ),
    )
    assert updated.default_cron == "0 4 * * *"
    assert updated.cron_timezone == "America/Chicago"
    assert updated.cron_timezone_resolved == "America/Chicago"
    assert updated.log_retention_days == 14
    assert updated.global_dry_run is False
    assert updated.exclude_ids["tmdb"] == ["42"]
    assert updated.exclude_ids["imdb"] == ["tt1"]

    loaded = get_app_settings(session)
    assert loaded.default_cron == "0 4 * * *"
    assert loaded.cron_timezone == "America/Chicago"
    assert loaded.global_dry_run is False


def test_update_local_cron_timezone_stores_device_zone(session: Session) -> None:
    ensure_defaults(session)
    updated = update_app_settings(
        session,
        AppSettings(
            default_cron="0 3 * * *",
            cron_timezone="local",
            cron_local_zone="America/Denver",
            log_retention_days=30,
            global_dry_run=True,
        ),
    )
    assert updated.cron_timezone == "local"
    assert updated.cron_local_zone == "America/Denver"
    assert updated.cron_timezone_resolved == "America/Denver"
