#!/usr/bin/env bash
# Dev backend entrypoint: migrate DB, then uvicorn with reload on bind-mounted source.
set -euo pipefail

log_step() { echo "[entrypoint-dev] $*" >&2; }

main() {
  log_step "Step 1/2: applying database migrations"
  alembic upgrade head

  log_step "Step 2/2: starting uvicorn with reload"
  exec uvicorn plextraktbox.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir plextraktbox \
    --use-colors
}

main "$@"
