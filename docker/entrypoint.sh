#!/usr/bin/env bash
# Container entrypoint: apply DB migrations, then launch the server.
# Steps: 1) run Alembic migrations  2) start uvicorn (serves API + SPA).
set -euo pipefail

log_step() { echo "[entrypoint] $*" >&2; }

main() {
  # Step 1: bring the SQLite schema up to date (idempotent).
  log_step "Step 1/2: applying database migrations"
  alembic upgrade head

  # Step 2: start the ASGI server on 0.0.0.0:8000.
  log_step "Step 2/2: starting uvicorn"
  exec uvicorn plextraktbox.main:app --host 0.0.0.0 --port 8000 --no-access-log
}

main "$@"
