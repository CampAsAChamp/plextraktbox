"""SESSION_HTTPS_ONLY resolution and adaptive Secure cookies."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from starlette.types import Scope

from plextraktbox import config
from plextraktbox.session_middleware import client_is_https, should_set_secure_cookie


@pytest.fixture(autouse=True)
def _clear_settings_cache(tmp_path: Path) -> None:
    os.environ["DATA_DIR"] = str(tmp_path)
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def test_default_mode_is_auto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.delenv("SESSION_HTTPS_ONLY", raising=False)
    settings = config.get_settings()
    assert settings.session_https_only_mode == "auto"


def test_local_also_defaults_to_auto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "local")
    monkeypatch.delenv("SESSION_HTTPS_ONLY", raising=False)
    settings = config.get_settings()
    assert settings.session_https_only_mode == "auto"


def test_explicit_false_is_never(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("SESSION_HTTPS_ONLY", "false")
    settings = config.get_settings()
    assert settings.session_https_only_mode == "never"


def test_explicit_true_is_always(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "local")
    monkeypatch.setenv("SESSION_HTTPS_ONLY", "true")
    settings = config.get_settings()
    assert settings.session_https_only_mode == "always"


def test_client_is_https_from_scheme() -> None:
    scope: Scope = {"type": "http", "scheme": "https", "headers": []}
    assert client_is_https(scope) is True


def test_client_is_https_from_forwarded_proto() -> None:
    scope: Scope = {
        "type": "http",
        "scheme": "http",
        "headers": [(b"x-forwarded-proto", b"https")],
    }
    assert client_is_https(scope) is True


def test_client_is_https_false_on_plain_http() -> None:
    scope: Scope = {"type": "http", "scheme": "http", "headers": []}
    assert client_is_https(scope) is False


def test_auto_secure_only_when_https() -> None:
    http_scope: Scope = {"type": "http", "scheme": "http", "headers": []}
    https_scope: Scope = {
        "type": "http",
        "scheme": "http",
        "headers": [(b"x-forwarded-proto", b"https,http")],
    }
    assert should_set_secure_cookie("auto", http_scope) is False
    assert should_set_secure_cookie("auto", https_scope) is True
    assert should_set_secure_cookie("always", http_scope) is True
    assert should_set_secure_cookie("never", https_scope) is False
