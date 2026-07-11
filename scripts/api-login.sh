#!/usr/bin/env bash
# Save an authenticated API session cookie jar for curl smoke tests.
#
# Steps:
# 1. Load optional defaults from .env (DEV_USER, DEV_PASSWORD, API_URL, API_COOKIES).
# 2. Prompt for username/password when not already set.
# 3. POST /api/auth/login and write cookies to cookies.txt.
# 4. Verify with GET /api/auth/me.

set -euo pipefail

log_step() {
  echo "[*] $*" >&2
}

require_jq() {
  # Side effect: exits non-zero when jq is not on PATH
  if ! command -v jq >/dev/null 2>&1; then
    echo "jq is required. Run: mise install (or brew install jq)" >&2
    exit 1
  fi
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

base_url="${API_URL:-http://localhost:8000}"
cookies_file="${API_COOKIES:-cookies.txt}"
username="${DEV_USER:-}"
password="${DEV_PASSWORD:-}"

read_username() {
  # Inputs: optional default username in $username
  # Outputs: sets $username
  if [[ -n "$username" ]]; then
    return
  fi
  read -r -p "Username or email: " username
  if [[ -z "$username" ]]; then
    echo "Username is required." >&2
    exit 1
  fi
}

read_password() {
  # Inputs: optional password in $password
  # Outputs: sets $password
  if [[ -n "$password" ]]; then
    return
  fi
  read -r -s -p "Password: " password
  echo >&2
  if [[ -z "$password" ]]; then
    echo "Password is required." >&2
    exit 1
  fi
}

build_login_payload() {
  # Inputs: $username, $password
  # Outputs: JSON payload on stdout
  jq -n --arg username "$username" --arg password "$password" \
    '{username: $username, password: $password}'
}

login_and_save_cookies() {
  # Inputs: $base_url, $cookies_file, login payload via $payload
  # Side effect: writes session cookies; exits non-zero on auth failure
  local payload="$1"
  local response
  local status

  response="$(curl -sS -w $'\n%{http_code}' -c "$cookies_file" \
    -X POST "$base_url/api/auth/login" \
    -H 'Content-Type: application/json' \
    -H 'X-Requested-With: XMLHttpRequest' \
    -d "$payload")"
  status="${response##*$'\n'}"
  response="${response%$'\n'*}"

  if [[ "$status" != "200" ]]; then
    rm -f "$cookies_file"
    echo "Login failed (HTTP $status): $response" >&2
    exit 1
  fi
}

verify_session() {
  # Inputs: $base_url, $cookies_file
  # Outputs: current user JSON on stdout; exits non-zero if session invalid
  curl -sS -f -b "$cookies_file" "$base_url/api/auth/me"
}

main() {
  require_jq

  # Step 1: collect credentials
  log_step "Collecting credentials"
  read_username
  read_password

  # Step 2: log in and save cookies
  log_step "Logging in at $base_url"
  payload="$(build_login_payload)"
  login_and_save_cookies "$payload"

  # Step 3: verify saved session
  log_step "Verifying session"
  user_json="$(verify_session)"
  username_out="$(jq -r '.username' <<< "$user_json")"
  log_step "Saved session to $cookies_file (logged in as $username_out)"
  echo "$user_json"
}

main "$@"
