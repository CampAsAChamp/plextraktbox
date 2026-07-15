# Phase 15 — Doppler secret management

**Status:** Planned

## Goal

Optional [Doppler](https://www.doppler.com/) integration for **maintainer** dev and CI workflows —
without making Doppler a runtime dependency for self-hosted TrueNAS users (`.env` / app config
remains the default).

## Deliverables

### Doppler project setup

- Doppler project + `dev` / `ci` configs mapping existing env vars:
  - `SECRET_KEY`
  - `TRAKT_CLIENT_ID`, `TRAKT_CLIENT_SECRET`
  - Other secrets from `.env.example`

### Repo integration

- `doppler.yaml` in repo root
- Document `doppler setup` + `doppler run` for local dev and `mise run up`
- Optional `doppler run --` wrapper tasks in `mise.toml`

### CI

- Service-token injection for integration tests that need real credentials
- No committed `.env` required for maintainers with Doppler CLI

### Production notes

- Entrypoint/compose notes for **optional** production injection (advanced users only)
- Self-hosted installs unchanged — `.env` or TrueNAS app config UI

## Prerequisites

[Phase 12](phase-12.md) CI restoration recommended; not blocked on TrueNAS phases

## Verification

Test plan TBD:

- Fresh clone with Doppler CLI → `doppler run mise run up` → health OK
- `doppler run mise run check` passes without hand-edited `.env`

**Next:** [Phase index](README.md) — Doppler is optional anytime; TrueNAS is phases 22–23 (last)
