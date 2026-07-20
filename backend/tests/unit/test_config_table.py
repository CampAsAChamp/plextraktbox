"""Public settings startup table — sorting and secret redaction."""

from __future__ import annotations

from pathlib import Path

import pytest

from plextraktbox.config import (
    Settings,
    format_public_settings_table,
    public_settings_rows,
)

SECRET_VALUE = "super-secret-value-must-not-appear"
TRAKT_ID = "trakt-client-id-abc123"
TRAKT_SECRET = "trakt-client-secret-xyz789"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        env="local",
        secret_key=SECRET_VALUE,
        data_dir=tmp_path,
        session_cookie="test_session",
        session_https_only=None,
        log_level="DEBUG",
        log_format="console",
        trakt_client_id=TRAKT_ID,
        trakt_client_secret=TRAKT_SECRET,
        sync_run_delay_seconds=1.5,
        flaresolverr_url="",
        flaresolverr_timeout_ms=30_000,
    )


def test_rows_are_sorted_case_insensitive(settings: Settings) -> None:
    names = [name for name, _ in public_settings_rows(settings)]
    assert names == sorted(names, key=str.casefold)


def test_secret_values_never_appear(settings: Settings) -> None:
    table = format_public_settings_table(settings)
    assert SECRET_VALUE not in table
    assert TRAKT_ID not in table
    assert TRAKT_SECRET not in table


def test_credentials_show_masked_when_present(settings: Settings) -> None:
    rows = dict(public_settings_rows(settings))
    assert rows["SECRET_KEY"] == "***"
    assert rows["TRAKT_CLIENT_ID"] == "***"
    assert rows["TRAKT_CLIENT_SECRET"] == "***"


def test_credentials_show_unset_when_empty(tmp_path: Path) -> None:
    settings = Settings(
        env="local",
        secret_key="local-secret",
        data_dir=tmp_path,
        trakt_client_id="",
        trakt_client_secret="",
    )
    rows = dict(public_settings_rows(settings))
    assert rows["TRAKT_CLIENT_ID"] == "unset"
    assert rows["TRAKT_CLIENT_SECRET"] == "unset"
    assert rows["SECRET_KEY"] == "***"


def test_empty_flaresolverr_renders_clearly(settings: Settings) -> None:
    rows = dict(public_settings_rows(settings))
    assert rows["FLARESOLVERR_URL"] == "(empty)"


def test_public_values_are_readable(settings: Settings, tmp_path: Path) -> None:
    rows = dict(public_settings_rows(settings))
    assert rows["ENV"] == "local"
    assert rows["LOG_LEVEL"] == "DEBUG"
    assert rows["LOG_FORMAT"] == "console"
    assert rows["SESSION_COOKIE"] == "test_session"
    assert rows["SESSION_HTTPS_ONLY"] == "auto"
    assert rows["SYNC_RUN_DELAY_SECONDS"] == "1.5"
    assert rows["FLARESOLVERR_TIMEOUT_MS"] == "30000"
    assert str(tmp_path.resolve()) in rows["DATA_DIR"]
    assert "plextraktbox.db" in rows["DATABASE_URL"]
    assert rows["VERSION"]
    assert rows["GIT_SHA"] == "(unset)"


def test_git_sha_from_environ(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLEXTRAKTBOX_GIT_SHA", "abc123def")
    rows = dict(public_settings_rows(settings))
    assert rows["GIT_SHA"] == "abc123def"


def test_host_port_defaults_when_unset(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    rows = dict(public_settings_rows(settings))
    assert rows["HOST"] == "0.0.0.0 (default)"
    assert rows["PORT"] == "8000 (default)"


def test_host_port_from_environ(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9000")
    rows = dict(public_settings_rows(settings))
    assert rows["HOST"] == "127.0.0.1"
    assert rows["PORT"] == "9000"


def test_table_has_header_and_aligned_columns(settings: Settings) -> None:
    table = format_public_settings_table(settings)
    lines = table.splitlines()
    assert lines[0].startswith("NAME")
    assert "VALUE" in lines[0]
    assert set(lines[1]) <= {"-", " "}
    assert any(line.startswith("ENV") for line in lines[2:])
