#!/usr/bin/env bash
# Run `mise run lint-fix` before an agent/task is allowed to complete.
# On failure, return followup_message so Cursor loops the agent to fix issues.
# On success (or skip), print {} so the turn can end.
set -euo pipefail

json_input=$(cat)

log() {
  printf '%s\n' "$*" >&2
}

emit_json() {
  printf '%s\n' "$1"
}

# Keep stdout reserved for the hook response JSON.
status="completed"
loop_count=0
if command -v python3 >/dev/null 2>&1; then
  eval "$(
    printf '%s' "$json_input" | python3 -c '
import json, shlex, sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
status = data.get("status") or "completed"
loop_count = data.get("loop_count", 0)
try:
    loop_count = int(loop_count)
except Exception:
    loop_count = 0
print(f"status={shlex.quote(str(status))}")
print(f"loop_count={shlex.quote(str(loop_count))}")
'
  )"
fi

if [[ "$status" != "completed" ]]; then
  log "lint-fix-on-stop: status=${status} — skipping"
  emit_json '{}'
  exit 0
fi

# Hooks inherit Cursor's PATH (bundled Node can break npm tooling). Prefer host tools.
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

# Skip when there is nothing in the working tree to format/lint.
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [[ -z "$(git status --porcelain --untracked-files=all -- backend frontend 2>/dev/null || true)" ]]; then
    log "lint-fix-on-stop: no backend/frontend changes — skipping"
    emit_json '{}'
    exit 0
  fi
fi

if ! command -v mise >/dev/null 2>&1; then
  log "lint-fix-on-stop: mise not found on PATH"
  emit_json '{"followup_message":"The stop hook could not run `mise run lint-fix` because `mise` was not found on PATH. Install/activate mise, then run `mise run lint-fix` and fix any remaining issues before finishing."}'
  exit 0
fi

log "lint-fix-on-stop: running mise run lint-fix (loop_count=${loop_count})"

tmp_out="$(mktemp)"
set +e
mise run lint-fix >"$tmp_out" 2>&1
exit_code=$?
set -e

if [[ "$exit_code" -eq 0 ]]; then
  log "lint-fix-on-stop: lint-fix succeeded"
  rm -f "$tmp_out"
  emit_json '{}'
  exit 0
fi

log "lint-fix-on-stop: lint-fix failed with exit ${exit_code}"

python3 - "$exit_code" "$tmp_out" <<'PY'
import json
import pathlib
import sys

exit_code = int(sys.argv[1])
raw = pathlib.Path(sys.argv[2]).read_text(errors="replace")
# Keep follow-up payloads bounded for context.
max_chars = 12000
if len(raw) > max_chars:
    raw = raw[:max_chars] + "\n...[truncated]...\n"

msg = (
    "Before marking this task complete, the project stop hook ran "
    "`mise run lint-fix` and it failed "
    f"(exit code {exit_code}).\n\n"
    "Fix the remaining lint/format issues (re-run `mise run lint-fix` "
    "locally if helpful), then continue. Do not consider the task done "
    "until lint-fix succeeds.\n\n"
    "```text\n"
    f"{raw}"
    "\n```"
)
print(json.dumps({"followup_message": msg}, ensure_ascii=False))
PY

rm -f "$tmp_out"
exit 0
