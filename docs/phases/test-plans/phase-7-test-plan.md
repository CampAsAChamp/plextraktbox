# Phase 7 verification checklist

**Scope:** [Phase 7](../phase-7.md)

Client-backed sources (movies): wire `PlexSource`, `TraktSource`, and `LetterboxdSource` to real
`clients/` fetch/apply; Plex library scoping, HTTP caching, pre-flight checks, and unmatched-item
reporting.

**Prerequisites:** [Phase 6](phase-6-test-plan.md) notifications passing; all four connections
`ok` in Settings. Shared setup: [testing.md](../../testing.md).

## What Phase 7 adds

- `fetch_watchlist` / `fetch_ratings` / `fetch_watched` call live APIs (**movies first**)
- `apply_*` writes to Plex and Trakt where reconcilers plan changes (Letterboxd stays read-only)
- TMDB client used for GUID resolution where sources need it
- **Plex library scoping** — library picker in Connections; selected libraries stored in
  `config_json`; `PlexSource` honors scope for watched/ratings fetch
- **HTTP caching** — `requests-cache` SQLite backend wired into client HTTP calls
- **Pre-flight check** — validate required connections are `ok` before creating a `JobRun`; clear
  API/UI error when a connection is missing or needs re-auth
- **Unmatched items report** — `RunSummary` tracks items with no cross-service identifier match;
  run-detail panel lists them for debugging
- Unit tests remain on fakes; new respx-backed tests for client → `MediaItem` mapping

## What Phase 7 defers to later phases

- Global settings, dry-run guards, exclude list, connection health job (Phase 8)
- Dashboard ops, schedule picker, clone/export (Phase 9)
- TV shows and episodes (Phase 10)
- TrueNAS packaging, GHCR, reverse proxy docs (Phase 11)

## 1. Automated tests

```bash
mise run test-backend    # unit tests on fakes + respx client mapping tests
mise run check           # CI parity before marking phase done
```

- [ ] Unit reconciler/engine tests still pass with fakes (no network)
- [ ] Respx tests cover Plex/Trakt/Letterboxd client responses → `MediaItem` fields
- [ ] Dry-run apply paths assert zero writes against mocked HTTP
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
- [ ] Disable dry-run on a small test job — verify writes land in Plex/Trakt (use caution)

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

- Letterboxd has no write API — `apply_*` on `LetterboxdSource` must remain unsupported
- Trakt token refresh on expiry should work via existing connection layer
- Per-item apply failures must not abort the run (existing engine behavior)
