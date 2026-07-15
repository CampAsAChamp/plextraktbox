# Phase 21 — Sync fetch & resolve caches

**Status:** Done

## Goal

Cut repeat work on sync runs: stop re-downloading / re-resolving the same Letterboxd, Trakt, and
Plex Discover data, and stop walking the Plex library multiple times in one run.

This does **not** change reconciler source-of-truth or add a Plex↔Trakt↔Letterboxd **match** table —
cross-service matching stays identifier-based and stateless. Caches cover **exports**, **list
fetches**, and **identifier / Discover key resolution** only.

## Deliverables

### Letterboxd CSV export cache

- Persist downloaded export CSVs under `{DATA_DIR}/caches/letterboxd/{connection_id}/`
- Reuse until TTL expires (default 24h) or the user forces refresh / clears cache
- Setting: `letterboxd_export_cache_ttl_hours` + Settings → Sync caches clear control
- Credentials change → invalidate export cache for that connection
- Run log: `sync.cache.letterboxd_export.hit|miss|forced`

### Letterboxd slug → identifiers cache

- SQLite table `letterboxd_slug_cache` (`slug` → tmdb/imdb + optional negative miss TTL)
- Resolver wraps TMDB/LB resolve; write-through on success; 1h negative cache on miss
- Clear via Settings → Sync caches

### Trakt list TTL cache

- SQLite table `trakt_list_cache` for watchlist / ratings / watched snapshots
- Default TTL 30 minutes (`trakt_list_cache_ttl_minutes`)
- Invalidate on successful apply that mutates the same list
- Run log: `sync.cache.trakt_list.hit|miss|forced|invalidated`

### Plex Discover key map

- SQLite table `plex_discover_key_cache` (`id_provider` + `external_id` + `libtype` → discover key)
- `rate_discover_movie` uses cached key; write-through after searchDiscover; invalidate on rate failure / not-found

### Plex library load once per run

- `PlexLibrarySnapshot` on `PlexSource` shares movies/shows + match-key indexes across fetch + apply
- Log once: `sync.plex.library.loaded`
- Not persisted across runs

### Ops / safety

- Durable caches on `/data` (files + SQLite)
- Settings UI: TTL controls + clear selected caches (`POST /api/settings/clear-sync-caches`)

## Key files

- `backend/plextraktbox/clients/plex_client.py` — `PlexLibrarySnapshot`; Discover key hooks
- `backend/plextraktbox/sync/sources/plex_source.py` — once-per-run library ownership
- `backend/plextraktbox/services/letterboxd_export_cache.py`
- `backend/plextraktbox/services/letterboxd_slug_cache.py`
- `backend/plextraktbox/services/trakt_list_cache.py`
- `backend/plextraktbox/services/plex_discover_key_cache.py`
- `backend/plextraktbox/services/sync_caches.py` — clear orchestration
- `backend/migrations/versions/009_sync_caches.py`
- `frontend/src/pages/Settings/SyncCachesSection.tsx`

## Out of scope

- Persisted Plex↔Trakt↔Letterboxd **match** table
- Long-lived Plex library snapshot across runs
- Letterboxd write-back
- Changing ratings / watchlist / watched source-of-truth

## Verification

[phase-21-test-plan.md](test-plans/phase-21-test-plan.md)

**Next:** [Phase index](README.md) — TrueNAS (22–23)
