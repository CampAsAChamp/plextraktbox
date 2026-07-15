# Phase 21 — Sync fetch & resolve caches

**Status:** Planned

## Goal

Cut repeat work on sync runs: stop re-downloading / re-resolving the same Letterboxd, Trakt, and
Plex Discover data, and stop walking the Plex library multiple times in one run.

This does **not** change reconciler source-of-truth or add a Plex↔Trakt↔Letterboxd **match** table —
cross-service matching stays identifier-based and stateless. Caches cover **exports**, **list
fetches**, and **identifier / Discover key resolution** only.

## Deliverables

### Letterboxd CSV export cache

- Persist the downloaded export (ratings / diary CSVs; watchlist optional) under `/data` or SQLite
- Reuse until TTL expires (default: e.g. 12–24h) or the user forces refresh
- Settings (or job override): `letterboxd_export_cache_ttl` + “Refresh Letterboxd export” action
- Still download on cache miss / expired / force; log cache hit vs miss in the run log
- Credentials change → invalidate export cache for that connection

### Letterboxd slug → identifiers cache

- Persist `letterboxd_slug` → `{tmdb, imdb?, …}` (and maybe title/year) in SQLite
- On fetch: resolve only uncached / invalid slugs; reuse hits without scraping LB or calling TMDB
- Write through on successful resolve; optional short-TTL on misses so bad resolves can retry
- Does not replace `MediaMatcher` — only speeds resolution before items enter matching

### Trakt list TTL cache

- Today Trakt watchlist / ratings / watched use bare `httpx` and bypass Phase 7 `requests-cache`
- Cache those list responses (or normalized `MediaItem` lists) with a short TTL (e.g. 15–60 min)
- Invalidate on successful apply that mutates the same list (watchlist add/remove, rate, etc.)
- Log cache hit vs miss; force-refresh path for debugging

### Plex Discover key map

- Persist `tmdb` / `imdb` (and maybe title+year fallback) → Discover metadata key
  (`plex://movie/…` id used by Discover rate / watchlist add)
- On apply: skip `searchDiscover` when the key is cached
- Write through after a successful Discover resolve; optional clear when rate/add fails with
  not-found

### Plex library load once per run

- Ratings fetch, watched fetch, and apply indexing each call `fetch_library_movies` today — large
  libraries pay 2–3 full scans per job
- Within a run: load scoped library movies **once**, share the raw videos / `MediaItem` list /
  match-key index across fetch + apply
- Prefer in-process / `SyncContext` sharing over a long-lived DB snapshot (library state should stay
  fresh across runs). Optional short HTTP TTL already exists via `requests-cache`; this deliverable
  is about **deduping work inside one run**

### Ops / safety

- Durable caches live on the `/data` volume (survive container restarts)
- Optional Settings clear-cache control (LB export, LB slug map, Trakt lists, Discover keys)
- Run-log metrics: per-cache hit/miss / newly resolved counts; library “loaded once” confirmation

### Testing

- Unit tests: cache hit skips download / TMDB / Trakt HTTP / Discover search; TTL expiry re-fetches;
  force refresh bypasses; apply mutations invalidate Trakt list cache
- Plex: one library `section.all()` (or equivalent) per run when ratings + watched + apply all run
- No change to reconciler plan outcomes when caches are warm vs cold (same effective MediaItems)

## Key files (expected)

- `backend/plextraktbox/clients/letterboxd_client.py` — export cache
- `backend/plextraktbox/clients/tmdb_client.py` / `sync/guid.py` — slug resolve via cache
- `backend/plextraktbox/clients/trakt_client.py` — list TTL (or shared list-cache helper)
- `backend/plextraktbox/clients/plex_client.py` — Discover key map; library load sharing hooks
- `backend/plextraktbox/sync/context.py` / `sync/sources/plex_source.py` — once-per-run library
- `backend/plextraktbox/models/` — resolve / Discover / export metadata tables
- `backend/migrations/` — new table(s)
- Settings UI / API when [Phase 13](phase-13.md) exists; until then: env/TTL defaults + force flag

## Prerequisites

[Phase 8](phase-8.md) — real movie sync (all of the above sit on the hot path)

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Global Settings TTL UI + clear-cache button | 13 (if Settings lands first, wire here; else ship defaults in 21) |
| HTTP `requests-cache` (~1h) for TMDB / LB film pages / Plex GETs | 7 (done) — complementary, not enough alone |

## Out of scope

- Persisted Plex↔Trakt↔Letterboxd **match** table (architecture stays stateless matching)
- Long-lived Plex library snapshot across runs (stale library ratings/watched are worse than a re-scan)
- Letterboxd write-back
- Changing ratings / watchlist / watched source-of-truth

## Verification

Test plan TBD when phase lands — copy
[phase-test-plan-template.md](test-plans/phase-test-plan-template.md).

**Next:** (end of product performance track for now — see [phases README](README.md))
