# Phase 6 — Notifications

**Status:** Done

## Goal

Notify the user when sync runs finish — Discord webhook and in-app bell — with global defaults and
per-job overrides.

## Deliverables

- **notification_config** model — channel (discord|inapp), enabled, on_success/on_failure, scope
  (global|job), encrypted webhook creds
- **inapp_notification** model — title, body, level, read flag, optional `run_id` link
- **notifications/dispatcher.py** — resolve job-override-else-global; fan out concurrently; isolated
  try/except per channel
- Discord embed via httpx (color by status); in-app row insert
- Settings → Notifications CRUD + **test** buttons
- Job form notification mode: inherit global / custom / disabled
- Navbar bell with unread count, mark read, links to runs
- `POST /api/notifications/{id}/test` synthetic payload

## Key files

- `backend/plextraktbox/notifications/`, `models/notification.py`, `inapp_notification.py`
- `frontend/src/pages/Settings` (notifications section), layout bell component

## Prerequisites

[Phase 5](phase-5.md)

## Defers to later phases

- Notification on connection `needs_reauth` (Phase 13)

## Verification

[phase-6-test-plan.md](test-plans/phase-6-test-plan.md)

**Next:** [Phase 7 — Client-backed fetch (movies)](phase-7.md) ← **current focus**
