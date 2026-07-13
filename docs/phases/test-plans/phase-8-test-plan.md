# Phase 8 verification checklist

**Scope:** [Phase 8](../phase-8.md)

Client-backed **apply** (movies): wire `PlexSource` and `TraktSource` `apply_*` to real APIs;
Letterboxd stays read-only.

**Prerequisites:** [Phase 7](phase-7-test-plan.md) fetch paths passing with real creds. Shared
setup: [testing.md](../../testing.md).

## What Phase 8 adds

- `PlexSource.apply_*` writes watchlist, ratings, and watched state (movies)
- `TraktSource.apply_*` writes where reconcilers plan changes (movies)
- `LetterboxdSource.apply_*` remains unsupported
- Respx tests for apply HTTP payloads; dry-run asserts zero writes

## What Phase 8 defers to later phases

- Global settings, dry-run guards, exclude list, connection health job (Phase 9)
- Dashboard ops, schedule picker, clone/export (Phase 10)
- TV shows and episodes (Phase 11)
- TrueNAS packaging, GHCR, reverse proxy docs (Phase 12)

## 1. Automated tests

```bash
mise run test-backend
mise run check
```

- [ ] Respx tests cover Plex/Trakt apply request shapes and success/error paths
- [ ] Dry-run apply paths assert zero writes against mocked HTTP
- [ ] Letterboxd `apply_*` still raises unsupported / no-op as designed
- [ ] Per-item apply failure does not abort the whole run

## 2. Container / browser (manual, real creds — use caution)

```bash
mise run up-dev
```

- [ ] Dry-run job still shows plans with zero writes (regression from Phase 7)
- [ ] Small test job with dry-run **off** — watchlist change lands in Trakt (or Plex per job)
- [ ] Ratings job (LB → Plex) with dry-run off — rating appears in Plex
- [ ] Watched job with dry-run off — watched state updates in Plex
- [ ] Re-run same job — idempotent / no duplicate spam in target service

## 3. Notes

- Use a tiny, reversible test library/watchlist before disabling dry-run
- Trakt token refresh on apply failure should surface in run logs
- Safety guards (first-run dry-run, exclude list) arrive in Phase 9
