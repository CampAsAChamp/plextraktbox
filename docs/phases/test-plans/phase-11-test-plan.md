# Phase 11 verification checklist

**Scope:** [Phase 11](../phase-11.md)

Client-backed **TV sync**: show watchlist (Plex ↔ Trakt) and episode-level watched (Trakt → Plex).
No TV ratings. Letterboxd stays film-only.

**Prerequisites:** [Phase 8](phase-8-test-plan.md) movie apply paths passing. Shared setup:
[testing.md](../../testing.md).

## What Phase 11 adds

- Show libraries selectable in Connections (alongside movies)
- Plex/Trakt watchlist fetch + apply for **shows**
- Episode-level Trakt watched → Plex `markWatched` for library episodes
- Episode match keys (`show id + S/E`); unmatched reports with `Show SxxExx` titles
- Run summary counters: `shows_added`, `shows_removed`, `episodes_watched`

## What Phase 11 defers

- TV / show ratings (any SoT) — out of scope
- Season-level watchlist or watched rollups
- Sync caches (Phase 21)
- Global settings, dry-run guards, exclude list (Phase 13)

## 1. Automated tests

```bash
mise run test-backend
mise run check
```

- [x] Matcher: episode S/E keys; movie does not match show with same id
- [x] Mappers: Trakt show/episode; Plex show/episode
- [x] `list_libraries` includes `type=show`
- [x] Trakt fetch watched-shows expands to episode items; watchlist shows mapped
- [x] Trakt apply watchlist posts `movies` + `shows` bodies
- [x] Plex mark watched covers episodes via library episode index
- [x] Reconciler: show watchlist add; episode watched; unmatched when no Plex library match
- [x] Dry-run apply paths still assert zero writes (existing movie tests + TV fakes)

## 2. Container / browser (manual, real creds — use caution)

```bash
mise run up-dev
```

### 2a. Library selection

- [ ] Connections → Plex libraries lists movie **and** show libraries with type labels
- [ ] Select at least one show library; save

### 2b. Dry-run (no writes)

- [ ] `plex_trakt` job with watchlist + watched; **dry-run on**
- [ ] Logs show planned show adds/removes and episode mark-watched ("would …")
- [ ] Confirm Plex / Trakt unchanged after the run

### 2c. Show watchlist (Plex → Trakt)

- [ ] Put a show on the **Plex** watchlist that is **not** on Trakt
- [ ] Live run (dry-run off) — show appears on Trakt; summary `shows_added` increments

### 2d. Episode watched (Trakt → Plex)

- [ ] Pick an episode watched on Trakt, present in a scoped show library, **unwatched** in Plex
- [ ] Live run — episode marked watched in Plex; summary `episodes_watched` increments
- [ ] Episode only on Trakt (not in library) → unmatched / skipped, no error abort

## 3. API smoke (optional)

```bash
mise run api-login
# trigger a plex_trakt job run; inspect /api/runs/{id} summary for shows_* / episodes_watched
```

## 4. Reset / fixtures

Use reversible show/episode pairs. Prefer dry-run first. Remove Trakt watchlist adds after testing
if undesired.

## Test fixtures

| Data type | Example | Setup |
| --------- | ------- | ----- |
| Show watchlist | *(pick one)* | On Plex watchlist; not on Trakt |
| Episode watched | *(pick one SxxExx)* | Watched on Trakt; in scoped show library; unwatched in Plex |
