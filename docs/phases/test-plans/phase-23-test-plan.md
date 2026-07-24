# Phase 23 test plan — TrueNAS App Catalog

Everything to verify **before** submitting plextraktbox to the TrueNAS App Catalog (or publishing
a custom catalog URL). Personal custom-app install must already be stable — see
[phase-22-test-plan.md](phase-22-test-plan.md), [deploy/truenas.md](../../deploy/truenas.md), and
[phase-23.md](../phase-23.md).

Use a **clean** TrueNAS SCALE instance (or a second app install on a fresh dataset) for catalog
verification so leftover state from the personal install cannot hide packaging bugs.

## Prerequisites (gate)

Do not start catalog packaging or submission until all of these are true:

- [ ] Personal install has run successfully on real TrueNAS hardware for a meaningful period
- [ ] Published image pulls without auth: `docker pull ghcr.io/campasachamp/plextraktbox:vX.Y.Z`
- [ ] GHCR package visibility is **Public** (or a documented registry credential exists for TrueNAS)
- [ ] `mise run check` passes on the release commit / tag you intend to ship
- [ ] Release notes / version tag match `backend/pyproject.toml` and the image tag

## Automated (CI / local)

- [ ] `mise run check` (lint, typecheck, pytest, vitest)
- [ ] Release workflow produced the expected GHCR tags (`vX.Y.Z` and `latest` if that is the
      release policy)
- [ ] Image is not a local-only / private-only tag the catalog cannot pull

## Catalog packaging

Confirm against the **current** TrueNAS SCALE app spec at submission time (format drifts across
releases):

- [ ] App definition (chart / `app.yaml`-style) validates with current TrueNAS tooling
- [ ] Config schema exposes user-facing fields (not raw env-only compose), including at least:
  - [ ] HTTP / host port (`PORT` + port mapping)
  - [ ] `/data` host dataset path → container `/data`
  - [ ] `SECRET_KEY`
  - [ ] `TRAKT_CLIENT_ID` / `TRAKT_CLIENT_SECRET`
  - [ ] Recommended `PUID` / `PGID`
  - [ ] Optional: `SESSION_HTTPS_ONLY`, `FLARESOLVERR_URL`, `FLARESOLVERR_TIMEOUT_MS`
- [ ] Defaults are safe: `ENV=prod` (or unset → image default); no `local`
- [ ] No host networking, privileged mode, or Docker socket mount
- [ ] Single container only; one published HTTP port
- [ ] Catalog / chart points at a **pinned** public image tag (`vX.Y.Z`), not a mutable local build
- [ ] App metadata (name, description, icon, version, maintainer) is complete and accurate
- [ ] Submission / review requirements for official community catalog **or** custom catalog URL
      are confirmed and met

## Clean catalog install

- [ ] Install from catalog UI on a clean SCALE box (or fresh dataset) with no prior plextraktbox
      state
- [ ] Config UI accepts required fields; app starts without manual compose edits
- [ ] Container becomes healthy / running; no crash loop
- [ ] SPA loads on the configured host port (`http://<nas-ip>:<port>`)
- [ ] Host path for `/data` is a ZFS dataset mount (survives app delete/recreate if dataset kept)
- [ ] Files under `/data` are owned by the configured `PUID`/`PGID` after first start

## First-run & auth

- [ ] Setup wizard appears on empty `/data`; creates the single admin user
- [ ] After setup, wizard is gone; login works; session survives refresh
- [ ] LAN HTTP login works with default `SESSION_HTTPS_ONLY=auto`
- [ ] If using Cloudflare Tunnel (or other HTTPS terminator): login over HTTPS works; session
      survives refresh; live log SSE works (see tunnel checklist in
      [deploy/truenas.md](../../deploy/truenas.md))

## Connections & sync smoke

- [ ] Connections: Plex, Trakt, Letterboxd, TMDB — save + connection test succeeds for each
- [ ] If Letterboxd hits Cloudflare challenges: FlareSolverr via UI (preferred) or env works from
      inside the container
- [ ] Create a job; dry-run produces "would …" logs and **zero** writes
- [ ] Live run (non-dry-run) completes; run history and live logs update
- [ ] Enable a schedule; confirm at least one cron fire (or temporary short cron for smoke)
- [ ] In-app notifications and/or Discord (if configured) after a run

## Persistence, upgrade, backup

- [ ] Stop / recreate app with **same** `/data` dataset + `SECRET_KEY` → login and connections
      still work (encrypted tokens remain valid)
- [ ] Bump catalog / image tag to a newer `vX.Y.Z` with same `/data` → migrations apply; app
      usable
- [ ] Delete app **without** deleting the dataset → reinstall → data still present
- [ ] Settings → Backup: download → restore same file → app usable after reload
- [ ] Restore while a sync run is active is rejected with a clear error
- [ ] Optional: ZFS snapshot of the `/data` dataset restores a known-good state

## Themes & settings (light)

- [ ] Default theme loads; custom CSS under `/data/themes` is discovered if present
- [ ] Settings pages load; no Doppler or maintainer-only tooling required at runtime

## Failure / constraint checks

- [ ] Missing `SECRET_KEY` or Trakt credentials fails clearly at install or first use (not a silent
      blank page)
- [ ] Partial `PUID`/`PGID` (only one set) is ignored with a logged warning; both set together
      works
- [ ] App does not require host networking, privileged mode, or Docker socket
- [ ] Catalog install does **not** depend on Doppler, corporate CA, or developer-only env

## Sign-off

| Check | Owner | Date | Notes |
| ----- | ----- | ---- | ----- |
| Prerequisites | | | |
| Packaging + image | | | |
| Clean catalog install | | | |
| First-run + sync smoke | | | |
| Upgrade + persistence | | | |
| Ready to submit | | | |

When all sections above are checked, proceed with catalog submission per
[phase-23.md](../phase-23.md).
