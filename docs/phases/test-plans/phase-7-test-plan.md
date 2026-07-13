# Phase 7 verification checklist

**Scope:** [Phase 7](../phase-7.md)

Client-backed **fetch** (movies): wire `PlexSource`, `TraktSource`, and `LetterboxdSource` to real
`clients/` fetch paths; Plex library scoping, HTTP caching, pre-flight checks, and unmatched-item
reporting. `apply_*` stays stubbed until [Phase 8](phase-8-test-plan.md).

**Prerequisites:** [Phase 6](phase-6-test-plan.md) notifications passing; all four connections
`ok` in Settings. Shared setup: [testing.md](../../testing.md).

## What Phase 7 adds

- `fetch_watchlist` / `fetch_ratings` / `fetch_watched` call live APIs (**movies first**)
- `apply_*` remains no-op / unsupported — dry-run shows plans only
- TMDB client used for GUID resolution where sources need it
- **Plex library scoping** — library picker in Connections; selected libraries stored in
  `config_json`; `PlexSource` honors scope for watched/ratings fetch
- **HTTP caching** — `requests-cache` SQLite backend wired into client HTTP calls
- **Pre-flight check** — validate required connections are `ok` before creating a `JobRun`; clear
  API/UI error when a connection is missing or needs re-auth
- **Unmatched items report** — `RunSummary` tracks items with no cross-service identifier match;
  run-detail panel lists them for debugging
- Unit tests remain on fakes; new respx-backed tests for client fetch → `MediaItem` mapping

## What Phase 7 defers to later phases

- `apply_*` writes to Plex and Trakt (Phase 8)
- Frontend prototype (Phase 9); full redesign (Phase 10)
- TV shows and episodes (Phase 11)
- Global settings, dry-run guards, exclude list, connection health job (Phase 12)
- Dashboard ops, schedule picker, clone/export (Phase 13)
- TrueNAS packaging, GHCR, reverse proxy docs (Phase 15)

## 1. Automated tests

```bash
mise run test-backend    # unit tests on fakes + respx client mapping tests
mise run check           # CI parity before marking phase done
```

- [ ] Unit reconciler/engine tests still pass with fakes (no network)
- [ ] Respx tests cover Plex/Trakt/Letterboxd client responses → `MediaItem` fields (fetch)
- [ ] Dry-run runs assert zero apply/write HTTP calls
- [ ] Pre-flight rejects run when a required connection is not `ok`
- [ ] Unmatched items appear in `RunSummary` when identifiers do not overlap

## 2. Container / browser (manual, real creds)

```bash
mise run up-dev          # or up + dev-bootstrap
```

- [ ] Plex Connections step: select which libraries to sync; selection persists after reload
- [ ] Create a **dry-run** Plex ↔ Trakt job (watchlist + watched)
- [ ] **Run now** — logs show fetched items (not empty fetches)
- [ ] Summary counts reflect matched/planned items (not all zeros)
- [ ] Run detail shows unmatched items when deliberately mismatched content exists
- [ ] Letterboxd → Plex ratings job (dry-run) shows LB ratings in plan logs
- [ ] Run with a broken connection — pre-flight error before run starts (no orphan `running` run)

## 3. API smoke (optional)

```bash
mise run api-login
curl -s -X POST -H 'X-Requested-With: XMLHttpRequest' -b cookies.txt \
  http://localhost:8000/api/jobs/{id}/run
```

## 4. Reset / fixtures

```bash
mise run dev-bootstrap   # after wipe; needs connection vars in .env
```

## 5. Notes

- Live writes are [Phase 8](phase-8-test-plan.md) — all runs in this phase should stay dry-run
- Trakt token refresh on expiry should work via existing connection layer
- Per-item apply failures must not abort the run (existing engine behavior; verified again in Phase 8)
