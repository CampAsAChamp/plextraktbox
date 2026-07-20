"""Package and build metadata for health checks and the UI.

Semver comes from ``backend/pyproject.toml`` (bumped by semantic-release).
"""

from __future__ import annotations

import os
import subprocess
import tomllib
from functools import lru_cache
from pathlib import Path

_ENV_GIT_SHA = "PLEXTRAKTBOX_GIT_SHA"
_ENV_BUILD_TIME = "PLEXTRAKTBOX_BUILD_TIME"
_REPO_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def package_version() -> str:
    """Installed package version, or pyproject.toml when running from a dev tree."""
    try:
        from importlib.metadata import version

        return version("plextraktbox")
    except Exception:
        pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        if pyproject.is_file():
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            project = data.get("project")
            if isinstance(project, dict):
                raw = project.get("version")
                if isinstance(raw, str) and raw:
                    return raw
        return "0.0.0.dev"


def git_sha() -> str | None:
    """Prefer ``PLEXTRAKTBOX_GIT_SHA`` (image builds); else ``git rev-parse`` in a checkout."""
    raw = os.environ.get(_ENV_GIT_SHA, "").strip()
    if raw:
        return raw
    return _git_sha_from_repo()


@lru_cache(maxsize=1)
def _git_sha_from_repo() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except OSError, subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    return sha or None


def built_at() -> str | None:
    raw = os.environ.get(_ENV_BUILD_TIME, "").strip()
    return raw or None


__version__ = package_version()
