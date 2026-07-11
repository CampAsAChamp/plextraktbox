# plextraktbox

Self-hosted Plex / Letterboxd / Trakt sync app. Single Docker container: FastAPI + React SPA + SQLite + APScheduler.

- **Design doc:** `PLAN.md` (architecture, phase tracker — source of truth for "why")
- **Agent guide:** `CLAUDE.md`
- **Testing:** `docs/testing.md` + `docs/phase-*-test-plan.md`

## Stack

Python 3.12 + FastAPI (backend), React 18 + Vite + Mantine (frontend). Tooling via `mise.toml`.

## Commands

```bash
mise run install       # deps
mise run dev-backend   # :8000
mise run dev-frontend  # :5173
mise run up-dev        # container hot reload
mise run test          # pytest + vitest
mise run check         # lint + typecheck + tests
mise run db-upgrade    # Alembic
```

## Principles

- Minimize scope; match existing code style.
- Only create git commits when the user asks.
- Run `mise run check` (or relevant subset) after substantive changes.
