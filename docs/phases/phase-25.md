# Phase 25 — Ops & OSS hygiene

**Status:** Done

## Goal

Close the remaining packaging and ops gaps from the post-product audit: open-source
hygiene files, Dependabot, SQLite backup restore, and clearer frontend error surfacing.

Phase 23 (TrueNAS catalog) stays independent and is not blocked by this work.

## Deliverables

### LICENSE

- Root [`LICENSE`](../../LICENSE) — MIT, matching `backend/pyproject.toml`

### SECURITY.md

- Supported versions (semver / GHCR tags)
- Private vulnerability reporting via GitHub Security Advisories
- Brief expected response window
- **Out of scope:** login rate limiting

### Dependabot

- [`.github/dependabot.yml`](../../.github/dependabot.yml) for `pip` (`backend/`), `npm`
  (`frontend/`), and `github-actions`
- Weekly schedule; group minor/patch updates where supported

### Backup restore

- Authenticated `POST /api/settings/backup/restore` (multipart `.db` upload)
- Validate SQLite + required app tables before replace
- Safe replace (dispose engine / pause scheduler; reject while a run is in progress)
- Settings UI with confirm dialog + toasts
- Document in [deploy/truenas.md](../deploy/truenas.md)

### Frontend error surfacing

- Notification bell: unread poll / list / mark-read failures → toast or inline error
- SSE log stream disconnect / error → user-visible feedback
- Prefer toast for actionable failures; keep healthy-state UI quiet

## Out of scope

- Phase 23 TrueNAS catalog
- Login rate limiting
- Docker `HEALTHCHECK`, Dependabot auto-merge, `CONTRIBUTING.md`, issue templates
- Browser E2E

## Verification

See [test-plans/phase-25-test-plan.md](test-plans/phase-25-test-plan.md).
