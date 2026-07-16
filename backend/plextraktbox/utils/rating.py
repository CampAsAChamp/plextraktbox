"""Rating scale conversions between services."""

from __future__ import annotations


def letterboxd_to_normalized(stars: float) -> float:
    """Convert Letterboxd 0.5–5 stars to Plex/Trakt 0–10 scale."""
    return round(stars * 2, 1)
