# Phase 7 — Client-backed sources (movies)

**Status:** Next

## Goal

Replace in-memory source stubs with real Plex, Trakt, and Letterboxd fetch/apply via `clients/` and
decrypted connection secrets — **movies first** — so dry-runs show real item counts and live runs
can sync data.

## Deliverables

### Live source wiring

- `source_factory` builds `PlexSource`, `TraktSource`, `LetterboxdSource` from `connection` rows
- `fetch_watchlist` / `fetch_ratings` / `fetch_watched` call live APIs (movies)
- `apply_*` writes to Plex and Trakt where reconcilers plan changes
- Letterboxd remains **read-only** — `apply_*` must stay unsupported
- TMDB client for GUID resolution where sources need it

### Plex library scoping

- Library picker in Connections UI
- Selected libraries stored in Plex `config_json`
- `PlexSource` honors scope for watched/ratings fetch

### HTTP caching

- `requests-cache` SQLite backend wired into client HTTP calls
- Reduces duplicate API traffic across runs

### Pre-flight checks

- Before creating a `JobRun`, validate required connections are `ok`
- Clear API/UI error when a connection is missing or needs re-auth (no orphan `running` runs)

### Unmatched items report

- `RunSummary` tracks items with no cross-service identifier match
- Run-detail panel lists unmatched items for debugging

### Testing strategy

- Unit tests stay on fakes + existing reconciler/engine tests
- New **respx** tests for client HTTP → `MediaItem` field mapping
- Manual dry-run with real creds shows non-zero fetch/plan counts

## Key files

- `backend/plextraktbox/sync/sources/plex_source.py`, `trakt_source.py`, `letterboxd_source.py`
- `backend/plextraktbox/services/source_factory.py`
- `backend/plextraktbox/clients/`
- `frontend` — Plex library picker in connections

## Prerequisites

[Phase 6](phase-6.md) — all four connections `ok`

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Global settings, dry-run guards, exclude list | 8 |
| Connection health monitoring job | 8 |
| Dashboard ops view, schedule picker | 9 |
| TV shows and episodes | 10 |
| TrueNAS packaging, GHCR, reverse proxy | 11 |

## Verification

[phase-7-test-plan.md](test-plans/phase-7-test-plan.md)

**Next:** [Phase 8 — Settings & operations](phase-8.md)
