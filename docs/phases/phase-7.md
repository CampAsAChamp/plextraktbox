# Phase 7 — Client-backed fetch (movies)

**Status:** Next

## Goal

Replace in-memory **fetch** stubs with real Plex, Trakt, and Letterboxd reads via `clients/` and
decrypted connection secrets — **movies first** — so dry-runs show real item counts and reconcile
plans against live data. `apply_*` stays stubbed until [Phase 8](phase-8.md).

## Deliverables

### Live fetch wiring

- `source_factory` builds `PlexSource`, `TraktSource`, `LetterboxdSource` from `connection` rows
- `fetch_watchlist` / `fetch_ratings` / `fetch_watched` call live APIs (movies)
- `apply_*` remains no-op / unsupported (existing Phase 3 behavior) — dry-run plans only
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
- New **respx** tests for client HTTP → `MediaItem` field mapping (fetch paths)
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
| `apply_*` writes to Plex and Trakt | 8 |
| Frontend prototype (run detail + logs) | 9 |
| Frontend redesign (full migration) | 10 |
| TV shows and episodes | 11 |
| Global settings, dry-run guards, exclude list | 13 |
| Connection health monitoring job | 13 |
| Dashboard ops view, schedule picker | 14 |
| TrueNAS packaging, GHCR, reverse proxy | 16 |

## Verification

[phase-7-test-plan.md](test-plans/phase-7-test-plan.md)

**Next:** [Phase 8 — Client-backed apply (movies)](phase-8.md)
