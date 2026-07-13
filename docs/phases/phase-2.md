# Phase 2 — Connections + wizard steps

**Status:** Done

## Goal

Persist encrypted credentials for Plex, Trakt, Letterboxd, and TMDB; guide the user through
onboarding; support re-auth when tokens expire.

## Deliverables

- **connection** model — `service`, `status`, `config_json` (non-secret), `secret_enc` (Fernet),
  `token_expires_at`
- Fernet encrypt/decrypt via `SECRET_KEY`-derived key (`security.py`)
- Four HTTP clients with `test_connection()`:
  - **Plex** — PIN auth flow, server discovery
  - **Trakt** — device OAuth (deployment-level `TRAKT_CLIENT_ID` / `TRAKT_CLIENT_SECRET`)
  - **Letterboxd** — username/password scrape auth
  - **TMDB** — API key
- Connections wizard steps in SPA + `needs_connections` gate after login
- Re-auth UI on dashboard ("Manage connections")
- API: connection status, save, test per service

## Key files

- `backend/plextraktbox/models/connection.py`, `clients/*_client.py`, `api/connections.py`
- `frontend/src/pages/SetupWizard/` (connection steps), connections page

## Prerequisites

[Phase 1](phase-1.md)

## Defers to later phases

- Plex library scoping picker (Phase 7)
- Scheduled connection health checks (Phase 12)
- Using connections in live sync fetches (Phase 7); apply (Phase 8)

## Verification

[phase-2-test-plan.md](test-plans/phase-2-test-plan.md)

**Next:** [Phase 3 — Sync engine core](phase-3.md)
