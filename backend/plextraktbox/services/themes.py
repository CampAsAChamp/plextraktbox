"""Built-in + custom UI theme registry (Phase 24)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from plextraktbox.config import get_settings

DEFAULT_THEME_ID = "cinema-night"
MAX_THEME_CSS_BYTES = 64 * 1024

BUILTIN_THEMES: tuple[tuple[str, str], ...] = (
    ("cinema-night", "Cinema Night"),
    ("one-dark-pro", "Atom One Dark Pro"),
    ("nord", "Nord"),
    ("dracula", "Dracula"),
)

BUILTIN_IDS: frozenset[str] = frozenset(theme_id for theme_id, _ in BUILTIN_THEMES)

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
_META_ID_RE = re.compile(r"@id:\s*([a-z0-9][a-z0-9-]{0,62})", re.IGNORECASE)
_META_NAME_RE = re.compile(r"@name:\s*(.+?)(?:\*/|$)", re.IGNORECASE)


@dataclass(frozen=True)
class ThemeInfo:
    id: str
    name: str
    source: str  # "builtin" | "custom"


def themes_dir() -> Path:
    path = get_settings().data_dir / "themes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_theme_id(raw: str) -> str:
    cleaned = re.sub(r"[^a-z0-9-]+", "-", raw.strip().lower()).strip("-")
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    if not cleaned or not _ID_RE.match(cleaned):
        raise ValueError("theme id must be lowercase alphanumeric with hyphens (max 63 chars)")
    return cleaned


def parse_theme_metadata(css: str, fallback_id: str) -> tuple[str, str]:
    """Return ``(id, name)`` parsed from CSS comment metadata."""
    theme_id = fallback_id
    name = fallback_id.replace("-", " ").title()

    id_match = _META_ID_RE.search(css)
    if id_match:
        theme_id = sanitize_theme_id(id_match.group(1))

    name_match = _META_NAME_RE.search(css)
    if name_match:
        name = name_match.group(1).strip()
        if not name:
            name = theme_id.replace("-", " ").title()

    return theme_id, name


def _safe_custom_path(theme_id: str) -> Path:
    """Resolve a custom theme file; reject path traversal."""
    safe_id = sanitize_theme_id(theme_id)
    if safe_id in BUILTIN_IDS:
        raise ValueError(f"theme id '{safe_id}' is reserved for a built-in theme")
    base = themes_dir().resolve()
    path = (base / f"{safe_id}.css").resolve()
    if path.parent != base:
        raise ValueError("invalid theme path")
    return path


def list_custom_themes() -> list[ThemeInfo]:
    results: list[ThemeInfo] = []
    directory = themes_dir()
    for path in sorted(directory.glob("*.css")):
        try:
            css = path.read_text(encoding="utf-8")
            fallback = sanitize_theme_id(path.stem)
            theme_id, name = parse_theme_metadata(css, fallback)
            if theme_id in BUILTIN_IDS:
                continue
            # Prefer filename id when metadata disagrees — one file per id on disk.
            disk_id = sanitize_theme_id(path.stem)
            results.append(ThemeInfo(id=disk_id, name=name, source="custom"))
        except OSError, UnicodeDecodeError, ValueError:
            continue
    return results


def list_themes() -> list[ThemeInfo]:
    built_ins = [ThemeInfo(id=tid, name=name, source="builtin") for tid, name in BUILTIN_THEMES]
    return [*built_ins, *list_custom_themes()]


def theme_exists(theme_id: str) -> bool:
    if theme_id in BUILTIN_IDS:
        return True
    try:
        return _safe_custom_path(theme_id).is_file()
    except ValueError:
        return False


def resolve_theme_id(theme_id: str | None) -> str:
    """Return a usable theme id, falling back to the factory default."""
    if theme_id and theme_exists(theme_id):
        return theme_id
    return DEFAULT_THEME_ID


def read_custom_css(theme_id: str) -> str:
    path = _safe_custom_path(theme_id)
    if not path.is_file():
        raise FileNotFoundError(theme_id)
    return path.read_text(encoding="utf-8")


def save_custom_theme(css: str, *, filename: str | None = None) -> ThemeInfo:
    """Validate and write a custom theme CSS file."""
    if not isinstance(css, str) or not css.strip():
        raise ValueError("theme CSS body is required")
    payload = css.encode("utf-8")
    if len(payload) > MAX_THEME_CSS_BYTES:
        raise ValueError(f"theme CSS exceeds {MAX_THEME_CSS_BYTES} bytes")

    fallback = "custom-theme"
    if filename:
        stem = Path(filename).name
        if "/" in stem or "\\" in stem or stem in (".", ".."):
            raise ValueError("invalid filename")
        if stem.lower().endswith(".css"):
            stem = stem[:-4]
        fallback = sanitize_theme_id(stem)

    theme_id, name = parse_theme_metadata(css, fallback)
    if theme_id in BUILTIN_IDS:
        raise ValueError(f"theme id '{theme_id}' is reserved for a built-in theme")

    path = _safe_custom_path(theme_id)
    path.write_text(css, encoding="utf-8")
    return ThemeInfo(id=theme_id, name=name, source="custom")


def delete_custom_theme(theme_id: str) -> None:
    if theme_id in BUILTIN_IDS:
        raise PermissionError("cannot delete a built-in theme")
    path = _safe_custom_path(theme_id)
    if not path.is_file():
        raise FileNotFoundError(theme_id)
    path.unlink()
