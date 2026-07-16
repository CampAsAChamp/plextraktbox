# plextraktbox

Self-hosted Plex / Letterboxd / Trakt sync app. Single Docker container: FastAPI + React SPA + SQLite + APScheduler.

- **Design doc:** `docs/architecture.md` (architecture, locked decisions — source of truth for "why")
- **Remaining work:** `docs/phases/README.md` (TrueNAS catalog)
- **Agent guide:** `CLAUDE.md`
- **Testing:** `docs/testing.md`
- **Dev workflow:** `docs/dev-workflow.md`

## Stack

Python 3.14 + FastAPI (backend), React 18 + Vite + Mantine (frontend). Tooling via `mise.toml`.

## Commands

Task groups appear in `mise tasks` as `[META]`, `[LOCAL]`, `[DOCKER-PROD]` (prod container), and `[DOCKER-DEV]` (dev containers).

```bash
mise run install       # deps
mise run dev-backend   # :8000 (override via PORT for prod compose)
mise run dev-frontend  # :5173
mise run up-dev        # container hot reload (Doppler)
mise run test          # pytest + vitest
mise run lint-fix     # autofix Ruff/ESLint + format (Ruff/Prettier)
mise run check         # lint + typecheck + tests
mise run db-upgrade    # Alembic
```

HTTP listen port defaults to **8000** (`PORT` env for prod compose / container).

## Principles

- Minimize scope; match existing code style.
- Only create git commits when the user asks.
- Run `mise run check` (or relevant subset) after substantive changes.
