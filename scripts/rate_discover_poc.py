#!/usr/bin/env python3
"""Proof-of-concept: rate a movie on Plex Discover (no library copy required).

Usage:
  cd backend && DATA_DIR=../data .venv/bin/python ../scripts/rate_discover_poc.py
  cd backend && DATA_DIR=../data .venv/bin/python ../scripts/rate_discover_poc.py --rating 9.0

Loads the Plex token from the app database (Connections). Requires SECRET_KEY + DATA_DIR.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

import httpx
from sqlmodel import Session, select

from plextraktbox.clients import plex_client
from plextraktbox.clients.media_mappers import media_item_from_plex_video
from plextraktbox.db import engine
from plextraktbox.models.connection import Connection, Service
from plextraktbox.services.connections import load_secrets
from plextraktbox.sync.media_item import MediaItem, MediaType


def _load_plex_token() -> str:
    with Session(engine) as session:
        connection = session.exec(select(Connection).where(Connection.service == Service.PLEX)).first()
        if connection is None:
            raise SystemExit("Plex connection not configured — complete Connections setup first")
        token = str(load_secrets(connection).get("token", ""))
        if not token:
            raise SystemExit("Plex token missing from connection secrets")
        return token


def main() -> None:
    parser = argparse.ArgumentParser(description="Rate a movie via Plex Discover (POC)")
    parser.add_argument("--title", default="The Social Network", help="Movie title for Discover search")
    parser.add_argument("--tmdb", default="37799", help="TMDB id for match verification")
    parser.add_argument("--rating", type=float, default=9.0, help="Rating on Plex 0–10 scale")
    parser.add_argument("--dry-run", action="store_true", help="Resolve only; do not write")
    args = parser.parse_args()

    token = _load_plex_token()
    item = MediaItem(
        title=args.title,
        media_type=MediaType.MOVIE,
        identifiers={"tmdb": str(args.tmdb)},
    )

    account = plex_client._plex_account(token)
    movie = plex_client._resolve_discover_movie(account, item)
    discover_key = plex_client._discover_metadata_key(movie)
    mapped = media_item_from_plex_video(movie)
    before = getattr(movie, "userRating", None)

    print(f"Resolved: {getattr(movie, 'title', args.title)!r}")
    print(f"  discover_key={discover_key}")
    print(f"  guid={getattr(movie, 'guid', '')}")
    print(f"  match_key={mapped.match_key() if mapped else None}")
    print(f"  current_user_rating={before}")
    print(f"  target_rating={args.rating}")

    if args.dry_run:
        print("Dry run — no write performed")
        return

    plex_client.rate_discover_movie_by_key(token, discover_key, args.rating)

    verify = httpx.get(
        f"{plex_client.PLEX_DISCOVER_BASE}/library/metadata/{discover_key}",
        headers={"X-Plex-Token": token, "Accept": "application/json"},
        params={"includeUserState": 1, "includeFields": "userRating"},
        timeout=15.0,
    )
    verify.raise_for_status()
    meta = verify.json()["MediaContainer"]["Metadata"][0]
    print(f"Rated via Discover — userRating now {meta.get('userRating')}")


if __name__ == "__main__":
    main()
