#!/bin/sh
# Dev frontend entrypoint: sync node_modules when package-lock.json changes, then Vite.
set -eu

LOCK_HASH_FILE="node_modules/.package-lock.sha256"

log_step() {
  echo "[entrypoint-dev-frontend] $*" >&2
}

sync_dependencies() {
  current_hash=$(sha256sum package-lock.json | awk '{print $1}')

  if [ -f "$LOCK_HASH_FILE" ] && [ "$(cat "$LOCK_HASH_FILE")" = "$current_hash" ]; then
    log_step "node_modules up to date"
    return 0
  fi

  log_step "package-lock.json changed; running npm ci"
  npm ci
  echo "$current_hash" > "$LOCK_HASH_FILE"
}

log_step "Step 1/2: syncing frontend dependencies"
sync_dependencies

log_step "Step 2/2: starting Vite dev server"
exec npm run dev -- --host 0.0.0.0
