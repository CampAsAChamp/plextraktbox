#!/usr/bin/env python3
"""Dev helpers for re-seeding user + service connections after wiping the DB.

Steps (bootstrap):
1. Load optional values from repo-root .env.
2. Create the admin user when /api/setup/status reports needs_setup.
3. Log in and save any connection credentials present in .env.
4. Print a summary of what was created, skipped, or missing.

Steps (export):
1. Read the local SQLite DB (DATA_DIR / SECRET_KEY from .env).
2. Print gitignored .env lines for user email and decrypted connection secrets.

Usage:
  backend/.venv/bin/python scripts/dev-bootstrap.py bootstrap
  backend/.venv/bin/python scripts/dev-bootstrap.py export
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from sqlmodel import Session, select

REPO_ROOT = Path(__file__).resolve().parent.parent
XHR_HEADERS = {"X-Requested-With": "XMLHttpRequest"}
LEGACY_SECRET_KEY = "dev"


def log_step(message: str) -> None:
    print(f"[*] {message}", file=sys.stderr)


def load_dotenv(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines from a dotenv file (no export keyword)."""
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


@dataclass(frozen=True)
class BootstrapConfig:
    base_url: str
    cookies_file: Path
    username: str
    email: str
    password: str
    plex_url: str | None
    plex_token: str | None
    tmdb_api_key: str | None
    letterboxd_username: str | None
    letterboxd_password: str | None
    trakt_access_token: str | None
    trakt_refresh_token: str | None
    wait_seconds: int
    force: bool


def read_bootstrap_config(env: dict[str, str], *, force: bool, wait_seconds: int) -> BootstrapConfig:
    """Build bootstrap settings from merged environment values."""
    username = env.get("DEV_USER", "").strip()
    password = env.get("DEV_PASSWORD", "").strip()
    if not username or not password:
        raise SystemExit(
            "Set DEV_USER and DEV_PASSWORD in .env "
            "(see .env.example)."
        )

    email = env.get("DEV_EMAIL", "").strip() or f"{username}@localhost"
    cookies_raw = env.get("API_COOKIES", "cookies.txt").strip() or "cookies.txt"
    cookies_file = Path(cookies_raw)
    if not cookies_file.is_absolute():
        cookies_file = REPO_ROOT / cookies_file

    return BootstrapConfig(
        base_url=env.get("API_URL", "http://localhost:8000").rstrip("/"),
        cookies_file=cookies_file,
        username=username,
        email=email,
        password=password,
        plex_url=_optional(env, "PLEX_URL"),
        plex_token=_optional(env, "PLEX_TOKEN"),
        tmdb_api_key=_optional(env, "TMDB_API_KEY"),
        letterboxd_username=_optional(env, "LETTERBOXD_USERNAME"),
        letterboxd_password=_optional(env, "LETTERBOXD_PASSWORD"),
        trakt_access_token=_optional(env, "TRAKT_ACCESS_TOKEN"),
        trakt_refresh_token=_optional(env, "TRAKT_REFRESH_TOKEN"),
        wait_seconds=wait_seconds,
        force=force,
    )


def _optional(env: dict[str, str], key: str) -> str | None:
    value = env.get(key, "").strip()
    return value or None


def configure_script_runtime(env: dict[str, str]) -> None:
    """Apply repo-root .env over mise task defaults before loading app settings."""
    import os

    os.chdir(REPO_ROOT)
    for key in ("ENV", "SECRET_KEY", "DATA_DIR", "TRAKT_CLIENT_ID", "TRAKT_CLIENT_SECRET"):
        if key in env:
            os.environ[key] = env[key]

    if "DATA_DIR" in env:
        data_dir = Path(env["DATA_DIR"])
        if not data_dir.is_absolute():
            data_dir = (REPO_ROOT / data_dir).resolve()
        os.environ["DATA_DIR"] = str(data_dir)


def resolve_settings(env: dict[str, str], *, data_dir: Path | None = None):
    """Load Settings after applying .env; optional data_dir overrides DATA_DIR."""
    import os

    configure_script_runtime(env)
    if data_dir is not None:
        os.environ["DATA_DIR"] = str(data_dir.resolve())

    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from plextraktbox import config

    config.get_settings.cache_clear()
    return config.get_settings()


def suggest_alternate_db(settings) -> Path | None:
    """When the chosen DB looks empty, point at a DB that has connections."""
    candidate = REPO_ROOT / "data" / "plextraktbox.db"
    chosen = settings.db_path.resolve()
    if not candidate.is_file() or candidate.resolve() == chosen:
        return None
    import sqlite3

    with sqlite3.connect(candidate) as conn:
        count = conn.execute("SELECT COUNT(*) FROM connection").fetchone()[0]
    if count:
        return candidate
    return None


def decrypt_secret_with_fallback(
    secret_enc: str,
    env: dict[str, str],
    *,
    data_dir: Path | None = None,
) -> tuple[str, bool]:
    """Decrypt using .env SECRET_KEY; fall back to legacy dev key. Returns (plaintext, used_legacy)."""
    from plextraktbox.security import InvalidToken, decrypt_secret

    resolve_settings(env, data_dir=data_dir)
    try:
        return decrypt_secret(secret_enc), False
    except InvalidToken:
        if env.get("SECRET_KEY", LEGACY_SECRET_KEY) == LEGACY_SECRET_KEY:
            raise
        resolve_settings({**env, "SECRET_KEY": LEGACY_SECRET_KEY}, data_dir=data_dir)
        from plextraktbox.security import decrypt_secret as legacy_decrypt

        return legacy_decrypt(secret_enc), True


def reencrypt_command(env: dict[str, str], *, data_dir: Path | None = None) -> None:
    """Re-encrypt connection secrets with the current .env SECRET_KEY."""
    settings = resolve_settings(env, data_dir=data_dir)
    log_step(f"Using database at {settings.db_path}")

    from plextraktbox.db import create_engine
    from plextraktbox.models.connection import Connection
    from plextraktbox.security import InvalidToken, encrypt_secret

    if not settings.db_path.is_file():
        raise SystemExit(f"No database at {settings.db_path}.")

    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )

    reencrypted = 0
    already_current = 0
    with Session(engine) as session:
        rows = session.exec(select(Connection)).all()
        if not rows:
            raise SystemExit("No connections in database.")

        for row in rows:
            if not row.secret_enc:
                continue
            try:
                plaintext, used_legacy = decrypt_secret_with_fallback(
                    row.secret_enc,
                    env,
                    data_dir=data_dir,
                )
            except InvalidToken as exc:
                raise SystemExit(
                    f"Could not decrypt {row.service} secrets. "
                    "Ensure SECRET_KEY in .env matches the app that wrote them."
                ) from exc

            if not used_legacy:
                already_current += 1
                continue

            resolve_settings(env, data_dir=data_dir)
            row.secret_enc = encrypt_secret(plaintext)
            session.add(row)
            reencrypted += 1
            log_step(f"Re-encrypted {row.service} secrets")

        if reencrypted:
            session.commit()

    if reencrypted:
        log_step(f"Done — re-encrypted {reencrypted} connection(s) with current SECRET_KEY.")
    else:
        log_step(
            f"Done — all {already_current} connection secret(s) already use current SECRET_KEY."
        )


def wait_for_api(client: httpx.Client, timeout_s: int) -> None:
    """Poll /api/health until the API responds or timeout expires."""
    if timeout_s <= 0:
        return
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            response = client.get("/api/health")
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    raise SystemExit(f"API at {client.base_url} did not become ready within {timeout_s}s")


def api_post(client: httpx.Client, path: str, payload: dict[str, Any] | None = None) -> httpx.Response:
    """POST JSON to the API with CSRF header."""
    return client.post(path, json=payload or {}, headers=XHR_HEADERS)


def ensure_user(client: httpx.Client, config: BootstrapConfig) -> str:
    """Create the setup user when needed. Returns 'created', 'exists', or raises."""
    status = client.get("/api/setup/status").json()
    if not status.get("needs_setup"):
        log_step("Setup already completed — skipping user creation")
        return "exists"

    log_step(f"Creating user {config.username!r}")
    response = api_post(
        client,
        "/api/setup/user",
        {
            "username": config.username,
            "email": config.email,
            "password": config.password,
        },
    )
    if response.status_code != 201:
        raise SystemExit(f"Setup failed ({response.status_code}): {response.text}")
    return "created"


def login(client: httpx.Client, config: BootstrapConfig) -> None:
    """Authenticate and persist session cookies to the cookie jar file."""
    log_step(f"Logging in as {config.username!r}")
    response = api_post(
        client,
        "/api/auth/login",
        {"username": config.username, "password": config.password},
    )
    if response.status_code != 200:
        raise SystemExit(f"Login failed ({response.status_code}): {response.text}")

    me = client.get("/api/auth/me")
    if me.status_code != 200:
        raise SystemExit("Login succeeded but /api/auth/me failed")
    log_step(f"Session saved to {config.cookies_file}")


def connection_map(client: httpx.Client) -> dict[str, str]:
    """Return service -> status for saved connections."""
    response = client.get("/api/connections/status")
    if response.status_code != 200:
        raise SystemExit(f"Could not read connection status ({response.status_code})")
    return {item["service"]: item["status"] for item in response.json()["connections"]}


def save_if_needed(
    client: httpx.Client,
    *,
    service: str,
    statuses: dict[str, str],
    force: bool,
    payload: dict[str, Any] | None,
    env_hint: str,
) -> str:
    """Save a connection when env creds exist. Returns action label."""
    if payload is None:
        log_step(f"{service}: skipped (set {env_hint} in .env to configure)")
        return "missing-env"

    current = statuses.get(service, "unconfigured")
    if current == "ok" and not force:
        log_step(f"{service}: already ok — skipped")
        return "skipped"

    log_step(f"{service}: saving connection")
    response = api_post(client, f"/api/connections/{service}", payload)
    if response.status_code != 200:
        raise SystemExit(f"{service} save failed ({response.status_code}): {response.text}")
    return "saved"


def save_trakt_if_needed(
    client: httpx.Client,
    config: BootstrapConfig,
    statuses: dict[str, str],
) -> str:
    """Trakt has no direct save endpoint; tokens are injected via a dev-only route."""
    if not config.trakt_access_token or not config.trakt_refresh_token:
        log_step("trakt: skipped (set TRAKT_ACCESS_TOKEN and "
                 "TRAKT_REFRESH_TOKEN in .env, or run export after UI auth)")
        return "missing-env"

    current = statuses.get("trakt", "unconfigured")
    if current == "ok" and not config.force:
        log_step("trakt: already ok — skipped")
        return "skipped"

    log_step("trakt: saving tokens")
    response = api_post(
        client,
        "/api/connections/trakt/tokens",
        {
            "access_token": config.trakt_access_token,
            "refresh_token": config.trakt_refresh_token,
        },
    )
    if response.status_code != 200:
        raise SystemExit(f"trakt save failed ({response.status_code}): {response.text}")
    return "saved"


def bootstrap_command(config: BootstrapConfig) -> None:
    """Run the full bootstrap workflow against a running API."""
    config.cookies_file.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(
        base_url=config.base_url,
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        # Step 1: wait for API
        log_step(f"Waiting for API at {config.base_url} (up to {config.wait_seconds}s)")
        wait_for_api(client, config.wait_seconds)

        # Step 2: create user if needed
        user_action = ensure_user(client, config)

        # Step 3: login (writes cookies.txt via manual export below)
        login(client, config)

        # Step 4: save connections
        statuses = connection_map(client)
        actions = {
            "plex": save_if_needed(
                client,
                service="plex",
                statuses=statuses,
                force=config.force,
                payload=(
                    {"url": config.plex_url, "token": config.plex_token}
                    if config.plex_url and config.plex_token
                    else None
                ),
                env_hint="PLEX_URL + PLEX_TOKEN",
            ),
            "tmdb": save_if_needed(
                client,
                service="tmdb",
                statuses=statuses,
                force=config.force,
                payload={"api_key": config.tmdb_api_key} if config.tmdb_api_key else None,
                env_hint="TMDB_API_KEY",
            ),
            "letterboxd": save_if_needed(
                client,
                service="letterboxd",
                statuses=statuses,
                force=config.force,
                payload=(
                    {
                        "username": config.letterboxd_username,
                        "password": config.letterboxd_password,
                    }
                    if config.letterboxd_username and config.letterboxd_password
                    else None
                ),
                env_hint="LETTERBOXD_USERNAME + LETTERBOXD_PASSWORD",
            ),
            "trakt": save_trakt_if_needed(client, config, statuses),
        }

        # Step 5: persist cookies for curl smoke tests
        _write_netscape_cookies(client, config.cookies_file)

        # Step 6: summary
        final = connection_map(client)
        log_step("Done.")
        print(
            json.dumps(
                {
                    "user": user_action,
                    "connections": actions,
                    "status": final,
                    "cookies_file": str(config.cookies_file),
                },
                indent=2,
            )
        )


def _write_netscape_cookies(client: httpx.Client, path: Path) -> None:
    """Write httpx cookies to a Netscape cookie jar file for curl."""
    if not client.cookies.jar:
        return
    lines = ["# Netscape HTTP Cookie File", "# Generated by scripts/dev-bootstrap.py"]
    for cookie in client.cookies.jar:
        domain = cookie.domain or ""
        include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
        cookie_path = cookie.path or "/"
        secure = "TRUE" if cookie.secure else "FALSE"
        expires = str(int(cookie.expires)) if cookie.expires else "0"
        lines.append(
            "\t".join(
                [
                    domain,
                    include_subdomains,
                    cookie_path,
                    secure,
                    expires,
                    cookie.name,
                    cookie.value or "",
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_command(env: dict[str, str], *, data_dir: Path | None = None) -> None:
    """Print .env lines for user email and decrypted connection secrets."""
    settings = resolve_settings(env, data_dir=data_dir)
    log_step(f"Using database at {settings.db_path}")

    from plextraktbox.db import create_engine
    from plextraktbox.models.connection import Connection
    from plextraktbox.models.user import User
    from plextraktbox.security import InvalidToken, decrypt_secret

    if not settings.db_path.is_file():
        alternate = suggest_alternate_db(settings)
        if alternate is not None:
            raise SystemExit(
                f"No database at {settings.db_path}. "
                f"Found connections in {alternate} — set DATA_DIR in .env or run:\n"
                f"  mise run dev-export-secrets -- --data-dir {alternate.parent}"
            )
        raise SystemExit(f"No database at {settings.db_path}. Complete setup in the UI first.")

    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )

    lines: list[str] = [
        "# Paste into .env after `mise run dev-export-secrets` (gitignored)",
        "# Re-run `mise run dev-bootstrap` after wiping ./data",
        "",
    ]

    with Session(engine) as session:
        user = session.exec(select(User).limit(1)).first()
        if user is None:
            raise SystemExit("No user in database — complete setup wizard first.")

        user_lines = [
            f"DEV_USER={user.username}",
            f"DEV_EMAIL={user.email}",
            "# Set password manually (stored as bcrypt hash in DB):",
            "# DEV_PASSWORD=your-password",
            "",
        ]
        lines.extend(user_lines)

        by_service = {row.service: row for row in session.exec(select(Connection)).all()}

        if not by_service:
            alternate = suggest_alternate_db(settings)
            if alternate is not None:
                raise SystemExit(
                    f"Database at {settings.db_path} has a user but no connections. "
                    f"Connections exist in {alternate} — set DATA_DIR=./data in .env "
                    f"(docker dev) or run:\n"
                    f"  mise run dev-export-secrets -- --data-dir {alternate.parent}"
                )

        try:
            _export_connections(by_service, lines, decrypt_secret)
        except InvalidToken:
            if env.get("SECRET_KEY", LEGACY_SECRET_KEY) == LEGACY_SECRET_KEY:
                raise SystemExit(
                    "Could not decrypt connection secrets. "
                    "Ensure SECRET_KEY in .env matches the running app."
                ) from None
            log_step(
                "Warning: tokens in the DB were encrypted with an older SECRET_KEY "
                f"({LEGACY_SECRET_KEY!r}); exporting via legacy decrypt. "
                "Run `mise run dev-reencrypt-secrets` once to fix the DB."
            )
            resolve_settings({**env, "SECRET_KEY": LEGACY_SECRET_KEY}, data_dir=data_dir)
            from plextraktbox.security import decrypt_secret as retry_decrypt

            lines[:] = [
                "# Paste into .env after `mise run dev-export-secrets` (gitignored)",
                "# Re-run `mise run dev-bootstrap` after wiping ./data",
                "",
                *user_lines,
            ]
            _export_connections(by_service, lines, retry_decrypt)
            lines.append(
                "# NOTE: DB tokens still use the legacy SECRET_KEY. "
                "Run `mise run dev-reencrypt-secrets`, then export again."
            )

    print("\n".join(lines))


def _export_connections(
    by_service: dict[Any, Any],
    lines: list[str],
    decrypt_secret: Any,
) -> None:
    from plextraktbox.models.connection import Service

    _export_plex(by_service.get(Service.PLEX), lines, decrypt_secret)
    _export_tmdb(by_service.get(Service.TMDB), lines, decrypt_secret)
    _export_letterboxd(by_service.get(Service.LETTERBOXD), lines, decrypt_secret)
    _export_trakt(by_service.get(Service.TRAKT), lines, decrypt_secret)


def _load_secrets(connection: Any, decrypt_secret: Any) -> dict[str, Any]:
    if connection is None or not connection.secret_enc:
        return {}
    data = json.loads(decrypt_secret(connection.secret_enc))
    return data if isinstance(data, dict) else {}


def _export_plex(connection: Any, lines: list[str], decrypt_secret: Any) -> None:
    if connection is None:
        lines.append("# Plex: not configured")
        return
    config = json.loads(connection.config_json or "{}")
    secrets = _load_secrets(connection, decrypt_secret)
    url = config.get("url", "")
    token = secrets.get("token", "")
    if url and token:
        lines.extend([f"PLEX_URL={url}", f"PLEX_TOKEN={token}", ""])
    else:
        lines.append("# Plex: incomplete config in DB")


def _export_tmdb(connection: Any, lines: list[str], decrypt_secret: Any) -> None:
    if connection is None:
        lines.append("# TMDB: not configured")
        return
    api_key = _load_secrets(connection, decrypt_secret).get("api_key", "")
    if api_key:
        lines.extend([f"TMDB_API_KEY={api_key}", ""])
    else:
        lines.append("# TMDB: no api_key in DB")


def _export_letterboxd(connection: Any, lines: list[str], decrypt_secret: Any) -> None:
    if connection is None:
        lines.append("# Letterboxd: not configured")
        return
    config = json.loads(connection.config_json or "{}")
    secrets = _load_secrets(connection, decrypt_secret)
    username = config.get("username", "")
    password = secrets.get("password", "")
    if username and password:
        lines.extend(
            [
                f"LETTERBOXD_USERNAME={username}",
                f"LETTERBOXD_PASSWORD={password}",
                "",
            ]
        )
    else:
        lines.append("# Letterboxd: incomplete config in DB")


def _export_trakt(connection: Any, lines: list[str], decrypt_secret: Any) -> None:
    if connection is None:
        lines.append("# Trakt: not configured")
        return
    secrets = _load_secrets(connection, decrypt_secret)
    access = secrets.get("access_token", "")
    refresh = secrets.get("refresh_token", "")
    if access and refresh:
        lines.extend(
            [
                f"TRAKT_ACCESS_TOKEN={access}",
                f"TRAKT_REFRESH_TOKEN={refresh}",
                "",
            ]
        )
    else:
        lines.append("# Trakt: incomplete tokens in DB")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dev bootstrap helpers for plextraktbox")
    sub = parser.add_subparsers(dest="command", required=True)

    bootstrap = sub.add_parser("bootstrap", help="Create user and connections from .env")
    bootstrap.add_argument(
        "--wait",
        type=int,
        default=30,
        metavar="SECONDS",
        help="Seconds to wait for the API to become ready (default: 30)",
    )
    bootstrap.add_argument(
        "--force",
        action="store_true",
        help="Re-save connections even when status is already ok",
    )

    sub.add_parser(
        "export",
        help="Print .env lines from the local SQLite DB (run once after UI setup)",
    )
    export = sub.choices["export"]
    export.add_argument(
        "--data-dir",
        type=Path,
        metavar="PATH",
        help="Override DATA_DIR (e.g. ./data for docker dev)",
    )

    reencrypt = sub.add_parser(
        "reencrypt",
        help="Re-encrypt DB connection secrets with current .env SECRET_KEY",
    )
    reencrypt.add_argument(
        "--data-dir",
        type=Path,
        metavar="PATH",
        help="Override DATA_DIR (default: from .env)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    env = load_dotenv(REPO_ROOT / ".env")

    if args.command == "export":
        log_step("Exporting dev credentials from local database")
        export_command(env, data_dir=args.data_dir)
        return

    if args.command == "reencrypt":
        log_step("Re-encrypting connection secrets with .env SECRET_KEY")
        reencrypt_command(env, data_dir=args.data_dir)
        return

    config = read_bootstrap_config(env, force=args.force, wait_seconds=args.wait)
    log_step("Bootstrapping dev environment from .env")
    bootstrap_command(config)


if __name__ == "__main__":
    main()
