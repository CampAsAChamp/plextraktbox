# Phase 22 test plan — TrueNAS personal install (custom app)

**Scope:** Custom app / "Launch Docker Image" on TrueNAS SCALE — GHCR pull, `PUID`/`PGID`, dataset
mount, first-run → sync → schedule → notifications, optional Cloudflare Tunnel. See
[phase-22.md](../phase-22.md) and [deploy/truenas.md](../../deploy/truenas.md).

**Out of scope:** App Catalog packaging and catalog UI install ([Phase 23](../phase-23.md)).

## 1. Automated / local checks

```bash
mise run check
```

- [ ] `mise run check` passes (especially after entrypoint / Dockerfile changes)
- [ ] Entrypoint PUID/PGID behavior matches [deploy/truenas.md](../../deploy/truenas.md)
      (`su-exec`, both required together)

### Local PUID smoke (Docker / Podman)

Prefer a **named volume** (macOS bind mounts often break UID visibility under rootless Podman):

```bash
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
podman top ptb-puid user pid comm   # expect non-root app user
podman exec ptb-puid ls -ln /data   # expect 1000:1000 on DB files
podman stop ptb-puid
podman volume rm ptb-puid-vol
```

- [ ] Health endpoint responds
- [ ] Process runs as the `PUID`/`PGID` user; SQLite owned by `1000:1000` inside the volume

## 2. GHCR pullability

```bash
docker pull ghcr.io/campasachamp/plextraktbox:vX.Y.Z
# or :latest — unauthenticated pull should succeed when the package is public
```

- [ ] Package visibility is **public** (or TrueNAS has a `ghcr.io` pull credential)
- [ ] Unauthenticated `docker pull` works from a clean environment

## 3. TrueNAS custom-app install (hardware)

Follow [deploy/truenas.md](../../deploy/truenas.md) step-by-step.

- [ ] ZFS dataset created; host path mounted at container `/data`
- [ ] Image from GHCR (prefer pinned `vX.Y.Z`)
- [ ] Env set: `SECRET_KEY`, `TRAKT_CLIENT_ID`, `TRAKT_CLIENT_SECRET`, matching `PUID`/`PGID`
- [ ] If overriding listen port: `PORT` and host/container port mapping all match
- [ ] `ENV` not set to `local` (image default `prod` is fine)
- [ ] No host network, privileged mode, or Docker socket
- [ ] Container stays up (no crash loop); SPA loads on the published host port
- [ ] Files under `/data` owned by configured `PUID`/`PGID` after first start

## 4. Product end-to-end on TrueNAS

- [ ] Setup wizard creates the single admin user
- [ ] Login works on LAN HTTP with default `SESSION_HTTPS_ONLY=auto`
- [ ] Connections: Plex, Trakt, Letterboxd, TMDB — save + connection test
- [ ] If Letterboxd Cloudflare-blocked: FlareSolverr via UI (or env) reachable from the container
- [ ] Dry-run job: "would …" logs and zero writes
- [ ] Live run completes; run history updates; live log SSE works
- [ ] Scheduled run fires (cron), or temporary short cron for smoke
- [ ] Discord and/or in-app notification after a completed run
- [ ] Optional: custom theme CSS under `/data/themes` loads

## 5. Persistence & upgrade

- [ ] Stop / recreate app with **same** `/data` + `SECRET_KEY` → login and connections still work
- [ ] Bump image tag to a newer `vX.Y.Z` with same `/data` → migrations apply; app usable
- [ ] Settings → Backup download → restore → app usable after reload (optional but recommended)

## 6. Cloudflare Tunnel HTTPS (recommended)

- [ ] Public hostname routes to `http://<nas-or-container>:<port>`
- [ ] Login via the HTTPS tunnel hostname; session survives refresh
- [ ] Live log SSE and the rest of the UI work through the tunnel
- [ ] LAN HTTP still works alongside the tunnel with default adaptive cookies

## 7. Docs

- [ ] [deploy/truenas.md](../../deploy/truenas.md) matches what you actually configured
- [ ] This checklist reflects any TrueNAS UI label changes you hit

## Notes

- Keep `SECRET_KEY` stable across upgrades or encrypted connection tokens will not decrypt.
- Prefer a pinned `vX.Y.Z` over `:latest` for reproducible upgrades.
- Catalog publication is out of scope — use
  [phase-23-test-plan.md](phase-23-test-plan.md) when ready for Milestone 2.

## Sign-off

| Check | Owner | Date | Notes |
| ----- | ----- | ---- | ----- |
| Local PUID + GHCR | | | |
| Custom-app install | | | |
| E2E sync + schedule | | | |
| Persistence / upgrade | | | |
| Tunnel (if used) | | | |
| Stable enough for Phase 23 | | | |
