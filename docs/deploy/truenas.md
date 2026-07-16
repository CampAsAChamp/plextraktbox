# Deploying on TrueNAS

The intended install target is **TrueNAS SCALE**, not just any Docker host. The container has been
kept dependency-free (single image, SQLite, one HTTP port) from Phase 0 so it drops into TrueNAS
without rework.

**Status:** Personal install ([Phase 22](../phases/phase-22.md)) is documented below. Catalog
publication is [Phase 23](../phases/phase-23.md) — do not start until this install has been stable.
[Phase 24](../phases/phase-24.md) (UI themes) is done — themes live under `/data/themes`.

## Design constraints (all environments)

These apply whenever touching Dockerfile, compose, or entrypoint — not only at deploy time:

- **Single container** — FastAPI serves the SPA, runs the scheduler, SQLite on `/data`
- **`/data` on a ZFS dataset** — host-path mount, not a Docker-managed volume, so the DB survives
  app reinstalls. Prefer ZFS snapshots of that dataset for routine backups; Settings also offers an
  ad-hoc SQLite download (`GET /api/settings/backup`).
- **One HTTP port** (8000) — no host networking, no privileged mode, no Docker-socket access
- **No hardcoded UIDs** — support `PUID`/`PGID` env vars so file ownership on the mounted dataset
  behaves on TrueNAS
- Ship via TrueNAS **Apps** (custom app / "Launch Docker Image" workflow, or catalog app later)
- **Secrets via app env / `.env`** — do not require [Doppler](https://www.doppler.com/). Doppler is
  optional for maintainers in local/CI only ([Phase 15](../phases/phase-15.md))

See [architecture.md](../architecture.md) for full stack context.

## Milestone 1 — Personal install (Phase 22)

Run the published image on your own TrueNAS box via **custom app** / "Launch Docker Image". No
catalog involvement — a working container + dataset mount on one machine.

## Milestone 2 — App Catalog (Phase 23)

Getting **plextraktbox** **listed in the TrueNAS App Catalog** is a separate, heavier effort. Do
**not** start until Phase 22 has run successfully on real hardware for a while.

**Catalog deliverables** (see [phase-23](../phases/phase-23.md)):

1. Package per current TrueNAS SCALE app spec (chart / `app.yaml`-style definition with config
   schema) — verify format at phase start; it changes across SCALE releases
2. Expose user-configurable options (HTTP port, `/data` path, `SECRET_KEY`, etc.) through the
   TrueNAS app config UI, not raw env-only compose
3. Publish container image to a public registry (e.g. GHCR) with versioned tags
4. Submit to the official community catalog or stand up a self-hosted custom catalog URL — confirm
   current submission/review requirements at the time
5. Verify catalog install on a clean TrueNAS instance

---

## GHCR image ([Phase 19](../phases/phase-19.md))

Published on each GitHub Release:

| Tag | Meaning |
| --- | ------- |
| `ghcr.io/campasachamp/plextraktbox:vX.Y.Z` | Immutable release matching `backend/pyproject.toml` |
| `ghcr.io/campasachamp/plextraktbox:latest` | Most recent stable release |

```bash
docker pull ghcr.io/campasachamp/plextraktbox:latest
```

The GitHub Packages container must be **public** for unauthenticated TrueNAS pulls. After the first
publish: GitHub → your profile → Packages → `plextraktbox` → Package settings → Change visibility →
**Public**. Direct settings URL pattern:
`https://github.com/users/<github-username>/packages/container/plextraktbox/settings`.

Until it is public, anonymous pulls fail (GHCR returns 403 for the pull token). Keep it private only
if you add a TrueNAS registry credential for `ghcr.io` (GitHub PAT with `read:packages`) under
Apps → Configuration → Registries.

---

## Step-by-step: custom app on TrueNAS SCALE

UI labels vary slightly across SCALE releases; map these fields to the current **Custom App** /
**Launch Docker Image** form.

### 1. Create a ZFS dataset for `/data`

Example path (adjust pool/dataset names to match your pool):

```text
/mnt/tank/apps/plextraktbox/data
```

In TrueNAS: **Datasets** → create `apps/plextraktbox/data` (or equivalent). Note the dataset’s
owner UID/GID (often the Apps user `568` / `apps` on recent SCALE builds). You will pass those as
`PUID` / `PGID`.

### 2. Launch the container

| Field | Value |
| ----- | ----- |
| Image | `ghcr.io/campasachamp/plextraktbox:vX.Y.Z` (prefer a pinned semver; or `:latest`) |
| Container port | `8000` |
| Host / node port | Choose a free port (e.g. `8000`) — tunnel origin uses this |
| Volume / storage | Host path → `/mnt/tank/apps/plextraktbox/data` mounted at container path `/data` |
| Restart policy | Unless stopped (or Always) |

**Environment variables:**

| Variable | Required | Notes |
| -------- | -------- | ----- |
| `SECRET_KEY` | Yes | Long random string; signs sessions and encrypts stored tokens. Generate once and keep stable: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `TRAKT_CLIENT_ID` | Yes | From your Trakt API app |
| `TRAKT_CLIENT_SECRET` | Yes | From your Trakt API app |
| `ENV` | No | Image default is `prod` (Secure session cookies). Do not set `local` on TrueNAS |
| `DATA_DIR` | No | Default `/data` — leave unset when using the mount above |
| `PUID` | Recommended | Host UID that should own files on the dataset (e.g. `568`) |
| `PGID` | Recommended | Host GID for that dataset (e.g. `568`) |

Do **not** enable host networking, privileged mode, or Docker socket mounts.

The published image does **not** include a corporate (Zscaler) CA — only public CAs. Developer
machines that need Zscaler for building use `USE_CORPORATE_CA=1` locally; see
[docker/certs/README.md](../../docker/certs/README.md).

### 3. `PUID` / `PGID` ownership

When both are set, the entrypoint:

1. Ensures a user/group with those IDs exists inside the container
2. `chown`s `/data` to that user
3. Runs migrations and uvicorn as that user (via `gosu`)

When unset, the process runs as the container’s default user (root in the published image) — fine for
local compose experiments, but on TrueNAS always set `PUID`/`PGID` to match the dataset ACL so
snapshots and host-side tools see consistent ownership.

Both must be set together; a partial pair is ignored with a warning.

### 4. First-run path

1. Open the app on the LAN port **or** (preferred) your Cloudflare Tunnel hostname — see below
2. Complete the setup wizard (create the single admin user)
3. Connect Plex, Trakt, Letterboxd, and TMDB under Connections
4. Create a job (start with dry-run), run it once, confirm logs
5. Enable a schedule; wait for a cron fire (or shorten the cron for a smoke test)
6. Configure Discord and/or confirm in-app notifications after a run

### 5. Upgrades

Bump the image tag to the new `vX.Y.Z` (or re-pull `:latest`) and recreate the app. Keep the same
`/data` dataset and `SECRET_KEY` so the DB and encrypted tokens remain valid.

---

## HTTPS via Cloudflare Tunnel

Prod images set `ENV=prod`, which enables **Secure** session cookies (`https_only`). The browser
must use an **HTTPS** hostname for login to stick — raw `http://nas:8000` will not keep the session
cookie.

Recommended path for this project: **Cloudflare Tunnel** (`cloudflared`) already running on TrueNAS
(or another always-on host), with a public hostname pointing at the plextraktbox origin.

### Tunnel route

In Zero Trust → Networks → Tunnels → your tunnel → Public Hostname:

| Setting | Example |
| ------- | ------- |
| Subdomain / domain | `plextraktbox.example.com` |
| Type | HTTP |
| URL / service | `http://<truenas-ip-or-hostname>:<host-port>` |

If `cloudflared` and plextraktbox share a Docker/Kubernetes network, you can use the container DNS
name instead of the NAS LAN IP, e.g. `http://plextraktbox:8000`.

Any other HTTPS terminator that forwards to port 8000 also works; cookies only require that the
browser sees HTTPS.

### Checklist

- [ ] Public hostname resolves and reaches the SPA
- [ ] Login via the tunnel hostname succeeds and the session survives refresh
- [ ] Live log SSE and the rest of the UI work over the tunnel

Do not put Cloudflare Access in front of the app unless you have a separate plan for API/SSE; the
app has its own session auth.

---

## Optional UI themes volume ([Phase 24](../phases/phase-24.md))

Custom theme CSS files are discovered from `{DATA_DIR}/themes/*.css` (same path as Settings
upload). With the usual `/data` mount that is already `/data/themes` inside the container — no
extra mount required. If you prefer a separate host folder:

```yaml
volumes:
  - /mnt/tank/apps/plextraktbox/data:/data
  # Optional second path only if themes live outside the main dataset:
  # - /mnt/tank/apps/plextraktbox/themes:/data/themes
```

Format notes: [phase-24.md](../phases/phase-24.md) and `frontend/src/themes/README.md`.

---

## Quick reference

| Setting | Value |
| ------- | ----- |
| Image | `ghcr.io/campasachamp/plextraktbox:vX.Y.Z` (or `:latest`) |
| Port | 8000 → app HTTP |
| Volume | Host ZFS path → `/data` |
| Env | `SECRET_KEY`, `TRAKT_CLIENT_ID`, `TRAKT_CLIENT_SECRET`, recommended `PUID`/`PGID` |
| HTTPS | Cloudflare Tunnel → `http://<host>:<port>` |

Verification checklist: [phase-22 test plan](../phases/test-plans/phase-22-test-plan.md).
