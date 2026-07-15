# Phase 15 — Doppler secret management

**Status:** Done

## Goal

Optional [Doppler](https://www.doppler.com/) integration for **maintainer** dev and CI workflows —
without making Doppler a runtime dependency for self-hosted TrueNAS users (`.env` / app config
remains the default).

## Deliverables

### Doppler project setup (manual, once)

In the [Doppler dashboard](https://dashboard.doppler.com/), create project **`plextraktbox`** with
configs **`local`** and **`ci`**.

| Config | Secrets | Notes |
| ------ | ------- | ----- |
| `local` | `SECRET_KEY`, `TRAKT_CLIENT_ID`, `TRAKT_CLIENT_SECRET` | Required for boot / Trakt OAuth app |
| `local` (optional) | `DEV_USER`, `DEV_EMAIL`, `DEV_PASSWORD`, `PLEX_URL`, `PLEX_TOKEN`, `TMDB_API_KEY`, `LETTERBOXD_USERNAME`, `LETTERBOXD_PASSWORD`, `TRAKT_ACCESS_TOKEN`, `TRAKT_REFRESH_TOKEN` | For `mise run dev-bootstrap` without a local `.env` |
| `ci` | Same bootstrap trio, or dummies | Default CI keeps stubbing `.env` in Actions; use a Doppler [service token](https://docs.doppler.com/docs/service-tokens) only for optional live-credential jobs |

Copy values from your existing gitignored `.env` (do not commit them). Prefer one stable
`SECRET_KEY` in `local` so Fernet-encrypted tokens in `./data` stay decryptable across machines.

### Repo integration

- [`doppler.yaml`](../../doppler.yaml) — project `plextraktbox`, default config `local`
- Maintainer `.env` keeps local knobs only; secrets live in Doppler
- Docs: [dev-workflow.md](../dev-workflow.md) § Doppler
- mise: `up-dev` / `rebuild-dev` / `api-login` / `dev-bootstrap` use Doppler; `up-dev-env` for `.env`-only; `up-doppler` / `check-doppler` also available

### CI

- Default [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) still stubs a dummy `.env`
  (no Doppler required for unit/e2e).
- Maintainers can run `mise run check-doppler` locally. Future integration jobs may set
  `DOPPLER_TOKEN` (service token scoped to `ci`) and wrap steps with `doppler run --`.

### Production notes

- Compose accepts secrets from `.env` **or** the host environment (`doppler run -- podman compose …`).
- TrueNAS / self-hosted installs stay on `.env` or the app-config UI — see
  [deploy/truenas.md](../deploy/truenas.md).

## Prerequisites

[Phase 12](phase-12.md) CI — done.

## Verification

See [test-plans/phase-15-test-plan.md](test-plans/phase-15-test-plan.md).

**Next:** [Phase index](README.md) — TrueNAS is phases 22–23; UI themes is Phase 24
