"""Package and build metadata for health checks and the UI.

Semver comes from ``backend/pyproject.toml`` (bumped by semantic-release).
"""

from __future__ import annotations

import os
import tomllib
from functools import lru_cache
from pathlib import Path

_ENV_GIT_SHA = "PLEXTRAKTBOX_GIT_SHA"
_ENV_BUILD_TIME = "PLEXTRAKTBOX_BUILD_TIME"


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
    raw = os.environ.get(_ENV_GIT_SHA, "").strip()
    return raw or None


def built_at() -> str | None:
    raw = os.environ.get(_ENV_BUILD_TIME, "").strip()
    return raw or None


__version__ = package_version()
