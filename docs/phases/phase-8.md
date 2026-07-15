# Phase 8 — Client-backed apply (movies)

**Status:** Done

## Goal

Wire `apply_*` on Plex and Trakt sources to real APIs so live runs (with dry-run off) can sync
movies — building on the fetch path proven in [Phase 7](phase-7.md). Letterboxd remains
**read-only** — `apply_*` must stay unsupported.

## Deliverables

### Live apply wiring

- `PlexSource.apply_*` writes watchlist, ratings, and watched state to Plex (movies)
- `TraktSource.apply_*` writes where reconcilers plan changes (movies)
- `LetterboxdSource.apply_*` stays unsupported (no write API)
- Dry-run continues to log "would …" with zero writes

### Testing strategy

- Respx tests for apply HTTP payloads and error handling
- Dry-run apply paths assert zero writes against mocked HTTP
- Manual live-run on a small test job verifies writes land in Plex/Trakt (use caution)

## Key files

- `backend/plextraktbox/sync/sources/plex_source.py`, `trakt_source.py`
- `backend/plextraktbox/clients/plex_client.py`, `trakt_client.py`
- Existing engine/reconciler tests — apply paths with fakes + respx

## Prerequisites

[Phase 7](phase-7.md) — real fetches and dry-run plans proven with live creds

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Frontend prototype (run detail + logs) | 9 |
| Frontend redesign (full migration) | 10 |
| TV shows and episodes | 11 |
| Global settings, dry-run guards, exclude list | 13 |
| Connection health monitoring job | 13 |
| Dashboard ops view, schedule picker | 14 |
| Doppler maintainer workflow | 15 |
| TrueNAS packaging, GHCR, reverse proxy | 22 |
| Sync fetch/resolve caches (LB, Trakt, Discover, Plex once-per-run) | 21 |

## Verification

[phase-8-test-plan.md](test-plans/phase-8-test-plan.md)

**Next:** [Phase 9 — Frontend prototype](phase-9.md)
