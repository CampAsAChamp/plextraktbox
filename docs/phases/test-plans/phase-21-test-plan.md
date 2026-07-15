# Phase 21 verification checklist

**Scope:** Sync fetch & resolve caches (LB export TTL, slug→ids, Trakt lists, Discover keys, Plex once-per-run library)

**Prerequisites:** Phases 0–8, 11–15, 18–20, 24 passing. Shared setup: [testing.md](../../testing.md).

## 1. Automated tests

```bash
mise run test-backend -- tests/unit/test_plex_library_snapshot.py \
  tests/unit/test_letterboxd_export_cache.py \
  tests/unit/test_letterboxd_slug_cache.py \
  tests/unit/test_trakt_list_cache.py \
  tests/unit/test_plex_discover_key_cache.py \
  tests/api/test_settings.py
mise run check
```

- [ ] `test_plex_library_snapshot` — movies loaded once for fetch + rate apply
- [ ] `test_letterboxd_export_cache` — hit / force / invalidate
- [ ] `test_letterboxd_slug_cache` — hit skips resolver; negative miss TTL
- [ ] `test_trakt_list_cache` — hit + invalidate
- [ ] `test_plex_discover_key_cache` — store / lookup / invalidate
- [ ] Settings GET/PUT includes cache TTLs; clear-sync-caches returns 200

## 2. Container / browser

```bash
mise run up-dev   # or mise run up after migrate
```

- [ ] Settings → Sync caches shows Letterboxd export TTL + Trakt list TTL
- [ ] Save cache settings persists and reloads
- [ ] Clear selected caches succeeds and toast shows counts
- [ ] Re-run a ratings job with warm LB export: run log shows `sync.cache.letterboxd_export.hit`
- [ ] Re-run with same Letterboxd slugs: fewer TMDB resolves (`sync.cache.letterboxd_slug.hit` in debug)
- [ ] Plex rate apply after fetch: single `sync.plex.library.loaded` for movies

## 3. API smoke (optional)

```bash
mise run api-login
curl -s -b cookies.txt http://localhost:8000/api/settings | jq '.letterboxd_export_cache_ttl_hours,.trakt_list_cache_ttl_minutes'
curl -s -b cookies.txt -X POST -H 'Content-Type: application/json' -H 'X-Requested-With: XMLHttpRequest' \
  -d '{"letterboxd_export":true,"letterboxd_slug":true,"trakt_lists":true,"discover_keys":true}' \
  http://localhost:8000/api/settings/clear-sync-caches
```

## 4. Reset / fixtures

```bash
# Wipe durable caches only (keeps app DB)
rm -rf data/caches/letterboxd
# Or clear via Settings UI / POST clear-sync-caches
# Full wipe: rm -rf data/ && mise run db-upgrade
```

## Notes

- HTTP `requests-cache` (Phase 7) remains complementary; it does not replace list/export/slug caches.
- Plex library snapshot is in-process per run only — intentional.
