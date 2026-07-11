#!/usr/bin/env bash
# Resolve podman compose or docker compose and forward all arguments.
#
# Steps:
# 1. Pick the available compose CLI (podman preferred).
# 2. exec the compose command with caller args unchanged.

set -euo pipefail

resolve_compose() {
  if command -v podman >/dev/null 2>&1; then
    echo "podman compose"
    return
  fi
  echo "docker compose"
}

main() {
  local compose
  compose=$(resolve_compose)
  # shellcheck disable=SC2086
  exec $compose "$@"
}

main "$@"
