# Phase 8 verification checklist

**Scope:** [Phase 8](../phase-8.md)

Client-backed **apply** (movies): wire `PlexSource` and `TraktSource` `apply_*` to real APIs;
Letterboxd stays read-only.

**Prerequisites:** [Phase 7](phase-7-test-plan.md) fetch paths passing with real creds. Shared
setup: [testing.md](../../testing.md).

## What Phase 8 adds

- `PlexSource.apply_*` writes watchlist, ratings, and watched state (movies)
- `TraktSource.apply_*` writes where reconcilers plan changes (movies)
- **Plex ratings fallback** — library `video.rate()` when the film is in a scoped library; else
  Plex Discover rate API (see [architecture.md](../../architecture.md#plex-ratings-discover-vs-library))
- `LetterboxdSource.apply_*` remains unsupported
- Respx tests for apply HTTP payloads; dry-run asserts zero writes

## What Phase 8 defers to later phases

- Frontend prototype (Phase 9); full redesign (Phase 10)
- TV shows and episodes (Phase 11)
- Global settings, dry-run guards, exclude list, connection health job (Phase 13)
- Dashboard ops, schedule picker, clone/export (Phase 14)
- TrueNAS packaging, GHCR, reverse proxy docs (Phase 16)

## 1. Automated tests

```bash
mise run test-backend
mise run check
```

- [x] Respx tests cover Plex/Trakt apply request shapes and success/error paths
- [x] Dry-run apply paths assert zero writes against mocked HTTP
- [x] Letterboxd `apply_*` still raises unsupported / no-op as designed
- [x] Per-item apply failure does not abort the whole run
- [x] Plex Discover rating path covered (`test_plex_discover_rate.py`)

## 2. Container / browser (manual, real creds — use caution)

```bash
mise run up-dev
```

Use the [test fixtures](#test-fixtures) below. Work one data type at a time; keep jobs small and
reversible.

### 2a. Dry-run regression (no writes)

- [ ] Create or reuse a job covering watchlist + ratings + watched (movies only)
- [ ] Run with **dry-run on** — logs show planned adds/removes/ratings/watched ("would …")
- [ ] Run summary counts look reasonable (not all zeros if fixtures exist)
- [ ] Confirm in target services (Plex / Trakt) that **nothing changed** after the run

### 2b. Watchlist (Plex → Trakt)

Source of truth: **Plex**. Trakt watchlist should be reconciled to match Plex.

Fixture: **Entergalactic** — on Plex watchlist, **not** on Trakt.

1. [ ] Dry-run watchlist job — log shows **add** Entergalactic to Trakt
2. [ ] Run same job with dry-run **off**
3. [ ] Trakt watchlist includes Entergalactic
4. [ ] Re-run — idempotent (no duplicate entries, no errors)
5. [ ] (Optional remove test) Remove from Plex watchlist, re-run — Trakt entry removed

### 2c. Ratings (Letterboxd → Plex + Trakt)

Source of truth: **Letterboxd**. Plex uses library rating when the film is in a scoped library;
otherwise **Discover** (account-level, not on a friend's shared server page).

#### Discover rating (not in library)

Fixture: **The Social Network** — rated on Letterboxd, **not** in your scoped Plex library.

1. [ ] Confirm film is absent from Connections-scoped libraries (may still appear on a shared server
      — that does not count)
2. [ ] Dry-run ratings job — log shows planned Plex rating for The Social Network (should **not**
      appear in unmatched-items as a Plex skip)
3. [ ] Run with dry-run **off**
4. [ ] Open Plex **Discover** detail for the film (`tv.plex.provider.discover`) — user rating
      matches Letterboxd (LB 0.5–5 ↔ Plex 0–10)
5. [ ] Trakt rating updated if the film exists in your Trakt ratings/history
6. [ ] Re-run — idempotent (rating unchanged, no errors)

#### Library rating (in scoped library)

Pick any LB-rated film you **own** in a scoped library with a missing or wrong Plex rating.

1. [ ] Dry-run — planned Plex rating update
2. [ ] Live run — rating on the **library** item in your server (not Discover)
3. [ ] Re-run — idempotent

### 2d. Watched (Trakt → Plex)

Source of truth: **Trakt**. Plex watched state applies only to films in scoped libraries.

Pick a film marked watched on Trakt, present in a scoped Plex library, unwatched in Plex.

1. [ ] Dry-run watched job — log shows planned mark-watched in Plex
2. [ ] Run with dry-run **off** — Plex library item shows watched
3. [ ] Re-run — idempotent

### 2e. Failure isolation

- [ ] If one item fails apply (e.g. bad id), run completes with errors counted; other items still
      applied

## 3. Notes

- Use a tiny, reversible test library/watchlist before disabling dry-run
- Plex Discover ratings appear on the Discover page, not on shared friends' library pages — expected
  Plex behavior ([architecture.md](../../architecture.md#plex-ratings-discover-vs-library))
- Trakt token refresh on apply failure should surface in run logs
- Safety guards (first-run dry-run, exclude list) arrive in Phase 13
- Optional debug script: `scripts/rate_discover_poc.py` (rates via Discover outside a full job)

## Test fixtures

Curated titles for manual runs. Adjust if your Letterboxd / Plex / Trakt state differs.

| Data type | Title | Setup |
| --------- | ----- | ----- |
| Watchlist | **Entergalactic** | On Plex watchlist; not on Trakt |
| Ratings (Discover) | **The Social Network** | Rated on Letterboxd; not in scoped Plex library |
| Ratings (library) | *(pick one)* | Rated on Letterboxd; in scoped library; missing/wrong Plex rating |
| Watched | *(pick one)* | Watched on Trakt; in scoped library; unwatched in Plex |
