# Phase 22 verification checklist

**Scope:** TrueNAS personal install — GHCR pull, `PUID`/`PGID`, custom-app docs, Cloudflare Tunnel
HTTPS — see [phase-22.md](../phase-22.md).

**Prerequisites:** Phases 0–8, 11–15, 18–21, 24 done; Phase 19 GHCR releases publishing. Shared
setup: [testing.md](../../testing.md). Deploy guide: [deploy/truenas.md](../../deploy/truenas.md).

## 1. Automated / local checks

```bash
mise run check
```

- [x] `mise run check` passes after entrypoint / Dockerfile changes
- [x] Entrypoint documents PUID/PGID behavior (`docker/entrypoint.sh`)

### Local PUID smoke (Docker / Podman)

Prefer a **named volume** (macOS bind mounts often break UID visibility under rootless Podman):

```bash
# Build an image that includes gosu + the Phase 22 entrypoint
SECRET_KEY=test TRAKT_CLIENT_ID=x TRAKT_CLIENT_SECRET=x podman compose build

podman volume create ptb-puid-vol
podman run --rm -d --name ptb-puid \
  -e SECRET_KEY=test-secret-key-for-puid-smoke-only \
  -e TRAKT_CLIENT_ID=unused \
  -e TRAKT_CLIENT_SECRET=unused \
  -e PUID=1000 \
  -e PGID=1000 \
  -p 18000:8000 \
  -v ptb-puid-vol:/data \
  localhost/plextraktbox:latest

curl -sf http://127.0.0.1:18000/api/health
podman top ptb-puid user pid comm   # expect USER=appuser
podman exec ptb-puid ls -ln /data   # expect 1000:1000 on plextraktbox.db
podman stop ptb-puid
podman volume rm ptb-puid-vol
```

- [x] Health endpoint responds
- [x] Process runs as `appuser` (`PUID`/`PGID`); SQLite owned by `1000:1000` inside the volume
- [ ] Restart keeps the same DB file (re-check after stop/start on TrueNAS)

## 2. GHCR pullability

```bash
docker pull ghcr.io/campasachamp/plextraktbox:latest
# Unauthenticated pull should succeed when the package is public
```

- [ ] Package visibility is **public** (or TrueNAS has a `ghcr.io` pull credential)
- [ ] Unauthenticated `docker pull` works from a clean environment

## 3. TrueNAS custom-app install (hardware)

Follow [deploy/truenas.md](../../deploy/truenas.md).

- [ ] ZFS dataset created and mounted at container `/data`
- [ ] Image pulled from GHCR (pinned `vX.Y.Z` or `:latest`)
- [ ] Env set: `SECRET_KEY`, Trakt client id/secret, matching `PUID`/`PGID`
- [ ] No host network, privileged mode, or Docker socket
- [ ] SPA loads on the published host port

## 4. Product end-to-end on TrueNAS

- [ ] Setup wizard creates the admin user
- [ ] Connections: Plex, Trakt, Letterboxd, TMDB configured
- [ ] Dry-run job succeeds; real job applies with per-item fault isolation
- [ ] Scheduled run fires (cron)
- [ ] Live log stream works for a run
- [ ] Discord and/or in-app notification after a completed run
- [ ] Optional: custom theme under `/data/themes` still loads ([Phase 24](../phase-24.md))

## 5. Cloudflare Tunnel HTTPS

- [ ] Public hostname routes to `http://<nas-or-container>:<port>`
- [ ] Login via the **HTTPS** tunnel hostname; session survives refresh (Secure cookies)
- [ ] UI (including SSE logs) usable through the tunnel

## 6. Docs

- [x] [deploy/truenas.md](../../deploy/truenas.md) has custom-app steps, ownership, tunnel, upgrades
- [x] [phase-22.md](../phase-22.md) marked Done and linked from [phases/README.md](../README.md)

## 7. Notes

- Prefer accessing the app through the tunnel hostname once HTTPS is configured; LAN HTTP will not
  keep Secure session cookies when `ENV=prod`.
- Keep `SECRET_KEY` stable across upgrades or encrypted connection tokens will not decrypt.
- Catalog publication is out of scope (Phase 23).
