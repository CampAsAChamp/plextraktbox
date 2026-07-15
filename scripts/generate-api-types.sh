#!/usr/bin/env bash
# Generate TypeScript types from the FastAPI OpenAPI schema.
#
# Steps:
# 1. Export OpenAPI JSON via create_app().openapi() (no server).
# 2. Run openapi-typescript to frontend/src/api/generated/schema.d.ts.
# 3. Remove the temporary OpenAPI JSON.

set -euo pipefail

log_step() {
  echo "[*] $*" >&2
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

openapi_tmp="$(mktemp -t plextraktbox-openapi.XXXXXX.json)"
cleanup() {
  rm -f "$openapi_tmp"
}
trap cleanup EXIT

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
  # Inputs: openapi_tmp. Outputs: frontend/src/api/generated/schema.d.ts
  log_step "Step 2/2: Generate TypeScript types"
  mkdir -p frontend/src/api/generated
  (
    cd frontend
    npx --yes openapi-typescript "$openapi_tmp" -o src/api/generated/schema.d.ts
  )
}

main() {
  if [[ ! -x backend/.venv/bin/python ]]; then
    echo "backend/.venv missing; run: mise run install-backend" >&2
    exit 1
  fi
  if [[ ! -d frontend/node_modules ]]; then
    echo "frontend/node_modules missing; run: mise run install-frontend" >&2
    exit 1
  fi

  export_openapi
  generate_typescript
  log_step "Done: frontend/src/api/generated/schema.d.ts"
}

main "$@"
