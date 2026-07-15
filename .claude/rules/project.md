# plextraktbox

Self-hosted Plex / Letterboxd / Trakt sync app. Single Docker container: FastAPI + React SPA + SQLite + APScheduler.

- **Design doc:** `docs/architecture.md` (architecture, locked decisions — source of truth for "why")
- **Phase index:** `docs/phases/README.md` (single progress table)
- **Agent guide:** `CLAUDE.md`
- **Testing:** `docs/testing.md` + `docs/phases/test-plans/`
- **Dev workflow:** `docs/dev-workflow.md`

## Stack

Python 3.14 + FastAPI (backend), React 18 + Vite + Mantine (frontend). Tooling via `mise.toml`.

## Commands

Task groups appear in `mise tasks` as `[META]`, `[LOCAL]`, `[DOCKER-PROD]` (prod container), and `[DOCKER-DEV]` (dev containers).

```bash
mise run install       # deps
mise run dev-backend   # :8000
mise run dev-frontend  # :5173
mise run up-dev        # container hot reload (Doppler)
mise run test          # pytest + vitest
mise run check         # lint + typecheck + tests
mise run db-upgrade    # Alembic
```

## Principles

- Minimize scope; match existing code style.
- Only create git commits when the user asks.
- Run `mise run check` (or relevant subset) after substantive changes.
