#!/usr/bin/env bash
# Generate TypeScript types from the FastAPI OpenAPI schema.
#
# Steps:
# 1. Export OpenAPI JSON via create_app().openapi() (no server).
# 2. Run openapi-typescript to a TypeScript output path.
# 3. In --check mode, diff against the committed schema without writing it.
# 4. Remove temporary files.
#
# Usage:
#   bash scripts/generate-api-types.sh          # write frontend/src/api/generated/schema.d.ts
#   bash scripts/generate-api-types.sh --check  # fail if committed types are out of date

set -euo pipefail

log_step() {
  echo "[*] $*" >&2
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

schema_path="frontend/src/api/generated/schema.d.ts"
check_only=0
openapi_tmp=""
schema_tmp=""

cleanup() {
  rm -f "$openapi_tmp" "$schema_tmp"
}
trap cleanup EXIT

usage() {
  cat >&2 <<'EOF'
Usage: bash scripts/generate-api-types.sh [--check]

  (default)  Write frontend/src/api/generated/schema.d.ts
  --check    Generate to a temp file and fail if it differs from the committed schema
EOF
}

parse_args() {
  # Inputs: "$@". Outputs: sets check_only.
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --check)
        check_only=1
        shift
        ;;
      -h | --help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown argument: $1" >&2
        usage
        exit 2
        ;;
    esac
  done
}

require_tooling() {
  # Inputs: none. Outputs: exits non-zero if backend/frontend deps are missing.
  if [[ ! -x backend/.venv/bin/python ]]; then
    echo "backend/.venv missing; run: mise run install-backend" >&2
    exit 1
  fi
  if [[ ! -d frontend/node_modules ]]; then
    echo "frontend/node_modules missing; run: mise run install-frontend" >&2
    exit 1
  fi
}

export_openapi() {
  # Inputs: repo_root, openapi_tmp. Outputs: writes OpenAPI JSON to openapi_tmp.
  log_step "Step 1/2: Export OpenAPI schema from FastAPI"
  ENV="${ENV:-local}" \
    SECRET_KEY="${SECRET_KEY:-generate-api-types-secret}" \
    TRAKT_CLIENT_ID="${TRAKT_CLIENT_ID:-cid}" \
    TRAKT_CLIENT_SECRET="${TRAKT_CLIENT_SECRET:-secret}" \
    DATA_DIR="${DATA_DIR:-$(mktemp -d)}" \
    backend/.venv/bin/python - <<'PY' "$openapi_tmp"
from __future__ import annotations

import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
from plextraktbox.main import create_app

schema = create_app().openapi()
out.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {out}", file=sys.stderr)
PY
}

generate_typescript() {
  # Inputs: openapi_tmp, output_path. Outputs: writes TypeScript types to output_path.
  local output_path="$1"
  log_step "Step 2/2: Generate TypeScript types"
  mkdir -p "$(dirname "$output_path")"
  (
    cd frontend
    npx --yes openapi-typescript "$openapi_tmp" -o "$output_path"
  )
}

check_schema_up_to_date() {
  # Inputs: schema_path, schema_tmp. Outputs: exits 1 if missing or drifted.
  if [[ ! -f "$schema_path" ]]; then
    echo "$schema_path missing; run: mise run generate-api-types" >&2
    exit 1
  fi
  if ! diff -u "$schema_path" "$schema_tmp" >&2; then
    echo "$schema_path is out of date; run: mise run generate-api-types" >&2
    exit 1
  fi
  log_step "Done: $schema_path is up to date"
}

write_schema() {
  # Inputs: schema_tmp, schema_path. Outputs: copies generated types into place.
  mkdir -p "$(dirname "$schema_path")"
  cp "$schema_tmp" "$schema_path"
  log_step "Done: $schema_path"
}

main() {
  # Step 1: parse args and verify tooling
  parse_args "$@"
  require_tooling

  openapi_tmp="$(mktemp -t plextraktbox-openapi.XXXXXX.json)"
  schema_tmp="$(mktemp -t plextraktbox-schema.XXXXXX.d.ts)"

  # Step 2: export OpenAPI and generate TypeScript into a temp file
  export_openapi
  # Pass an absolute -o path so openapi-typescript does not write under frontend/.
  generate_typescript "$schema_tmp"

  # Step 3: either verify drift or write the committed schema
  if [[ "$check_only" -eq 1 ]]; then
    check_schema_up_to_date
  else
    write_schema
  fi
}

main "$@"
