---
paths:
  - backend/plextraktbox/sync/**/*
---

# Sync engine

Ported from PlexTraktSync patterns: GUID matching, stateless diffing, dry-run, pluggy plugins.
Sync fetch/resolve caches (LB export + slug→ids, Trakt lists, Discover keys, Plex once-per-run
library) are Phase 21 — not a cross-service match table.

## Source of truth

| Data type | Truth | Direction |
| --------- | ----- | --------- |
| Watchlist | Plex | Reconcile Trakt to match Plex (LB watchlist ignored) |
| Ratings | Letterboxd | Push → Plex + Trakt |
| Watched | Trakt | Mark watched in Plex |

Letterboxd is **read-only** — never add write-back to Letterboxd. Watchlist sync does not
fetch or use the Letterboxd watchlist.

## Architecture

- `sources/` — per-service read/write adapters (`Source` ABC)
- `reconcilers/` — per-data-type plan + apply logic
- `engine.py` — orchestrates fetch → plan → log → apply → `RunSummary`
- `guid.py` / `matcher.py` — identifier matching (TMDB → IMDb → TVDB)
- `plugins.py` — pluggy hook seam for future extensions

## Rules

- Dry-run must log "would …" and skip all `apply_*` calls
- Per-item try/except on apply — one failure ≠ abort run
- Use fakes in tests; no live API calls in unit tests
