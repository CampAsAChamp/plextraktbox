# Phase 1 — Auth + wizard (user)

**Status:** Done

## Goal

Single local admin account with a first-run setup wizard, session-based auth, and SPA routing gates
so the app is usable before connections or sync exist.

## Deliverables

- **user** model — username, email, `password_hash` (bcrypt); single row enforced in app
- Starlette `SessionMiddleware` + auth dependency gating all routes except setup/health
- Setup API: `GET /api/setup/status`, `POST /api/setup/user` (self-disables once user exists)
- Auth API: `POST /api/auth/login`, `logout`, `GET /api/auth/me`
- CSRF mitigation: require `X-Requested-With` on mutating requests
- SPA gates: no user → `/setup`; user but not logged in → `/login`; else → dashboard
- Gravatar-derived `avatar_url` on auth responses from email

## Key files

- `backend/plextraktbox/models/user.py`, `security.py`, `api/auth.py`, `api/setup.py`
- `frontend/src/pages/SetupWizard/`, `Login`, `App.tsx` (router + gates)

## Prerequisites

[Phase 0](phase-0.md)

## Defers to later phases

- Service connections (Phase 2)
- Fernet encryption for third-party tokens (Phase 2)

## Verification

[phase-1-test-plan.md](test-plans/phase-1-test-plan.md)

**Next:** [Phase 2 — Connections](phase-2.md)
