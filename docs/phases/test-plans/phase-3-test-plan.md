# Phase 3 verification checklist

**Scope:** [Phase 3](../phase-3.md)

Sync engine core: MediaItem/guid/matcher, sources, three source-of-truth reconcilers,
engine with dry-run, and temporary synchronous `POST /api/jobs/{id}/run`.

**Prerequisites:** [Phase 2](phase-2-test-plan.md) passing. Shared setup: [testing.md](../../testing.md).

## 1. Automated tests

```bash
mise run test-backend    # tests/unit/test_guid.py, test_matcher.py, test_reconciler_*.py,
                         # test_engine.py, tests/api/test_jobs.py
# or: mise run test
mise run check           # CI parity before marking phase done
```

Covers: GUID parsing, cross-service matching, watchlist (Plex truth), ratings (Letterboxd
truth), watched (Trakt truth), dry-run = zero writes, job CRUD + manual run API.

## 2. API smoke (optional)

Create a session cookie jar first (see [testing.md](../../testing.md#api-smoke-sessions)):

```bash
mise run api-login
```

Then:

```bash
curl -s -b cookies.txt http://localhost:8000/api/jobs
# → []

curl -s -X POST http://localhost:8000/api/jobs \
  -H 'Content-Type: application/json' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -b cookies.txt \
  -d '{"name":"Plex ↔ Trakt","source_pair":"plex_trakt","data_types":["watchlist","watched"],"dry_run":true}'
# → job JSON with id

curl -s -X POST http://localhost:8000/api/jobs/1/run \
  -H 'X-Requested-With: XMLHttpRequest' \
  -b cookies.txt
# → JobRunResponse with status success (empty sources until client fetch lands)
```

## 3. Notes

- Sources use in-memory adapters in Phase 3; client-backed fetch/apply is [Phase 7](phase-7-test-plan.md).
- Reconcilers enforce source-of-truth: watchlist=Plex, ratings=Letterboxd, watched=Trakt.
- Letterboxd is read-only (`apply_*` raises `NotSupported`).
- Full scheduler, run history UI, and live logs arrive in Phases 4–5.
