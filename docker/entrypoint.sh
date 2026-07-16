#!/usr/bin/env bash
# Container entrypoint: optional PUID/PGID, migrate DB, then launch the server.
# Steps: 1) drop privileges setup  2) Alembic migrations  3) uvicorn (API + SPA).
set -euo pipefail

DATA_DIR="${DATA_DIR:-/data}"
PUID="${PUID:-}"
PGID="${PGID:-}"

log_step() { echo "[entrypoint] $*" >&2; }

# Inputs: PUID, PGID env. Side effects: creates/updates appuser/appgroup; chowns DATA_DIR.
configure_permissions() {
  local uid="$1" gid="$2"

  if ! getent group "$gid" >/dev/null 2>&1; then
    groupadd --non-unique -g "$gid" appgroup
  fi

  if ! getent passwd "$uid" >/dev/null 2>&1; then
    useradd --non-unique -u "$uid" -g "$gid" -M -d /app -s /usr/sbin/nologin appuser
  else
    usermod -g "$gid" "$(getent passwd "$uid" | cut -d: -f1)" 2>/dev/null || true
  fi

  mkdir -p "$DATA_DIR"
  chown -R "${uid}:${gid}" "$DATA_DIR"
}

# Run a command as PUID:PGID when set; otherwise as current user (usually root).
run_privileged_or_user() {
  if [[ -n "$PUID" && -n "$PGID" ]]; then
    su-exec "${PUID}:${PGID}" "$@"
  else
    "$@"
  fi
}

main() {
  mkdir -p "$DATA_DIR"

  # Step 1: optional linuxserver-style UID/GID for ZFS host-path mounts.
  if [[ -n "$PUID" || -n "$PGID" ]]; then
    if [[ -z "$PUID" || -z "$PGID" ]]; then
      log_step "WARNING: both PUID and PGID must be set; ignoring partial values"
    else
      log_step "Step 1/3: configuring permissions PUID=${PUID} PGID=${PGID}"
      configure_permissions "$PUID" "$PGID"
    fi
  else
    log_step "Step 1/3: PUID/PGID unset — running as container user ($(id -u):$(id -g))"
  fi

  # Step 2: bring the SQLite schema up to date (idempotent).
  log_step "Step 2/3: applying database migrations"
  run_privileged_or_user alembic upgrade head

  # Step 3: start the ASGI server (PORT defaults to 8000; override via env).
  PORT="${PORT:-8000}"
  log_step "Step 3/3: starting uvicorn on 0.0.0.0:${PORT}"
  if [[ -n "$PUID" && -n "$PGID" ]]; then
    exec su-exec "${PUID}:${PGID}" uvicorn plextraktbox.main:app --host 0.0.0.0 --port "${PORT}" --no-access-log
  fi
  exec uvicorn plextraktbox.main:app --host 0.0.0.0 --port "${PORT}" --no-access-log
}

main "$@"
