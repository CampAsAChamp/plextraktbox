"""Gravatar profile image URLs derived from user email."""

from __future__ import annotations

import hashlib


def gravatar_url(email: str, *, size: int = 80) -> str:
    """Return a Gravatar avatar URL for the given email address."""
    normalized = email.strip().lower()
    digest = hashlib.md5(normalized.encode(), usedforsecurity=False).hexdigest()
    return f"https://www.gravatar.com/avatar/{digest}?s={size}&d=identicon"
