"""Tests for package version and build metadata resolution."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from plextraktbox import version_info

_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


@pytest.fixture(autouse=True)
def _clear_git_sha_cache() -> None:
    version_info._git_sha_from_repo.cache_clear()


def test_package_version_matches_pyproject() -> None:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    expected = data["project"]["version"]
    assert version_info.package_version() == expected


def test_git_sha_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLEXTRAKTBOX_GIT_SHA", "abc123def456")
    assert version_info.git_sha() == "abc123def456"


def test_git_sha_falls_back_to_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PLEXTRAKTBOX_GIT_SHA", raising=False)
    monkeypatch.setattr(version_info, "_git_sha_from_repo", lambda: "fedcba987654")
    assert version_info.git_sha() == "fedcba987654"


def test_git_sha_empty_when_unset_and_no_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PLEXTRAKTBOX_GIT_SHA", raising=False)
    monkeypatch.setattr(version_info, "_git_sha_from_repo", lambda: None)
    assert version_info.git_sha() is None


def test_built_at_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLEXTRAKTBOX_BUILD_TIME", "2026-07-13T04:00:00Z")
    assert version_info.built_at() == "2026-07-13T04:00:00Z"
