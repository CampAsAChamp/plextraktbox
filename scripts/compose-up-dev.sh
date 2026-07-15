#!/usr/bin/env bash
# Foreground hot-reload stack that waits for a clean teardown on Ctrl+C.
#
# Steps:
# 1. Start `podman compose up` (optional Doppler + --build) in the background.
# 2. Wait until compose exits or the user hits Ctrl+C.
# 3. On interrupt/exit, run `compose down` and wait so shutdown logs never
#    spill into the next shell prompt (mise/doppler otherwise return too early).
#
# Env:
#   USE_DOPPLER=1 (default) — wrap with `doppler run --`
#   BUILD=1 (default) — pass `--build` to `compose up`
#   COMPOSE_FILE — defaults to docker-compose.dev.yml

set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
USE_DOPPLER="${USE_DOPPLER:-1}"
BUILD="${BUILD:-1}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

log_step() {
  echo "[*] $*" >&2
}

up_pid=""
shutting_down=0

compose() {
  # Inputs: compose subcommand + args. Side effect: talks to Podman.
  podman compose -f "$COMPOSE_FILE" "$@"
}

# Invoked via trap (shellcheck cannot see that).
# shellcheck disable=SC2329
shutdown() {
  # Ordered teardown; ignores further Ctrl+C so we finish before the prompt returns.
  if [[ "$shutting_down" -eq 1 ]]; then
    return
  fi
  shutting_down=1
  trap '' INT TERM

  echo >&2
  log_step "Stopping dev stack (waiting for containers)…"
  compose down --remove-orphans || true

  if [[ -n "$up_pid" ]] && kill -0 "$up_pid" 2>/dev/null; then
    kill "$up_pid" 2>/dev/null || true
    wait "$up_pid" 2>/dev/null || true
  fi

  log_step "Dev stack stopped."
  exit 130
}

main() {
  # Step 1: start compose in the background so we can trap Ctrl+C under `wait`.
  local -a up_args=(up)
  if [[ "$BUILD" == "1" ]]; then
    up_args+=(--build)
  fi

  trap shutdown INT TERM

  if [[ "$USE_DOPPLER" == "1" ]]; then
    log_step "Starting hot-reload stack (Doppler)…"
    doppler run -- podman compose -f "$COMPOSE_FILE" "${up_args[@]}" &
  else
    log_step "Starting hot-reload stack (.env)…"
    compose "${up_args[@]}" &
  fi
  up_pid=$!

  # Step 2: block until compose exits or SIGINT/SIGTERM hits `wait`.
  local status=0
  set +e
  wait "$up_pid"
  status=$?
  set -e

  # Step 3: ensure containers/networks are fully gone before we return.
  trap - INT TERM
  if [[ "$shutting_down" -eq 0 ]]; then
    shutting_down=1
    log_step "Compose exited; finishing teardown…"
    compose down --remove-orphans || true
    log_step "Dev stack stopped."
  fi

  exit "$status"
}

main "$@"
