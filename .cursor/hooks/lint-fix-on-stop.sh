#!/usr/bin/env bash
# Run `mise run lint-fix` when an agent turn completes (same chat only).
# Always returns {} — never emits followup_message, which can open a new agent.
#
# Steps:
# 1. Skip aborted/error stops
# 2. Sanitize PATH / locate repo
# 3. Skip if backend/frontend are clean
# 4. Run mise run lint-fix; log result to stderr
set -euo pipefail

json_input=$(cat)

log() {
  printf '%s\n' "$*" >&2
}

emit_ok() {
  printf '%s\n' '{}'
}

# Step 1: parse status; only run on completed turns.
status="completed"
if command -v python3 >/dev/null 2>&1; then
  status="$(
    printf '%s' "$json_input" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
print(data.get("status") or "completed")
'
  )"
fi

if [[ "$status" != "completed" ]]; then
  log "lint-fix-on-stop: status=${status} — skipping"
  emit_ok
  exit 0
fi

# Step 2: prefer host tools over Cursor's bundled Node.
if command -v python3 >/dev/null 2>&1; then
  PATH="$(
    python3 -c '
import os
skip = (".cursor-server", ".vscode-server", "Cursor.app")
print(":".join(
    p for p in os.environ.get("PATH", "").split(":")
    if p and not any(s in p for s in skip)
))
'
  )"
  export PATH
fi
export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# Step 3: skip when there is nothing to format/lint.
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [[ -z "$(git status --porcelain --untracked-files=all -- backend frontend 2>/dev/null || true)" ]]; then
    log "lint-fix-on-stop: no backend/frontend changes — skipping"
    emit_ok
    exit 0
  fi
fi

if ! command -v mise >/dev/null 2>&1; then
  log "lint-fix-on-stop: mise not found on PATH — skipping"
  emit_ok
  exit 0
fi

# Step 4: autofix in place; never follow up into another agent.
log "lint-fix-on-stop: running mise run lint-fix"
tmp_out="$(mktemp)"
trap 'rm -f "$tmp_out"' EXIT

set +e
mise run lint-fix >"$tmp_out" 2>&1
exit_code=$?
set -e

if [[ "$exit_code" -eq 0 ]]; then
  log "lint-fix-on-stop: lint-fix succeeded"
else
  log "lint-fix-on-stop: lint-fix failed with exit ${exit_code}"
  # Truncate for the Hooks output channel; agent must re-run / fix in this chat.
  head -c 8000 "$tmp_out" >&2 || true
  printf '\n' >&2
fi

emit_ok
exit 0
