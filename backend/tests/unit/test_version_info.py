"""Tests for package version and build metadata resolution."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from plextraktbox import version_info

_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def test_package_version_matches_pyproject() -> None:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    expected = data["project"]["version"]
    assert version_info.package_version() == expected


def test_git_sha_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLEXTRAKTBOX_GIT_SHA", "abc123def456")
    assert version_info.git_sha() == "abc123def456"


def test_git_sha_empty_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PLEXTRAKTBOX_GIT_SHA", raising=False)
    assert version_info.git_sha() is None


def test_built_at_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLEXTRAKTBOX_BUILD_TIME", "2026-07-13T04:00:00Z")
    assert version_info.built_at() == "2026-07-13T04:00:00Z"
