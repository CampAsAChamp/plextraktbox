"""Unit tests for theme registry helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from plextraktbox.services import themes as themes_svc


def test_sanitize_theme_id() -> None:
    assert themes_svc.sanitize_theme_id("Ocean Night") == "ocean-night"
    # Path-ish input is stripped to a safe slug (then path.resolve guards traversal).
    assert themes_svc.sanitize_theme_id("../escape") == "escape"
    with pytest.raises(ValueError):
        themes_svc.sanitize_theme_id("")


def test_parse_metadata() -> None:
    css = "/* @name: Soft Gray */\n/* @id: soft-gray */\nbody {}\n"
    theme_id, name = themes_svc.parse_theme_metadata(css, "fallback")
    assert theme_id == "soft-gray"
    assert name == "Soft Gray"


def test_save_and_delete_custom(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    # Reload settings if cached — get_settings typically reads env each call via lru.
    from plextraktbox.config import get_settings

    get_settings.cache_clear()
    try:
        css = "/* @name: Test */\n/* @id: test-theme */\n:root { --x: 1; }\n"
        info = themes_svc.save_custom_theme(css)
        assert info.id == "test-theme"
        assert themes_svc.theme_exists("test-theme")
        assert "Test" in themes_svc.read_custom_css("test-theme")
        themes_svc.delete_custom_theme("test-theme")
        assert not themes_svc.theme_exists("test-theme")
        assert themes_svc.resolve_theme_id("test-theme") == themes_svc.DEFAULT_THEME_ID
    finally:
        get_settings.cache_clear()


def test_resolve_builtin() -> None:
    assert themes_svc.resolve_theme_id("nord") == "nord"
    assert themes_svc.resolve_theme_id(None) == "cinema-night"
    assert themes_svc.resolve_theme_id("missing") == "cinema-night"
