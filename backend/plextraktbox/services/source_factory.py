"""Build sync sources from configured connections."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import structlog
from sqlmodel import Session

if TYPE_CHECKING:
    from structlog.stdlib import BoundLogger

from plextraktbox.clients import tmdb_client
from plextraktbox.config import get_settings
from plextraktbox.models.connection import ConnectionStatus, Service
from plextraktbox.models.job import Job
from plextraktbox.services import connections as conn_svc
from plextraktbox.sync.sources.base import Source
from plextraktbox.sync.sources.letterboxd_source import LetterboxdSource
from plextraktbox.sync.sources.plex_source import PlexSource
from plextraktbox.sync.sources.trakt_source import TraktSource


def _connection_ok(session: Session, service: Service) -> bool:
    connection = conn_svc.get_connection(session, service)
    return connection is not None and connection.status == ConnectionStatus.OK


def _plex_library_ids(config: dict) -> list[str]:
    libraries = config.get("libraries") or []
    if not isinstance(libraries, list):
        return []
    ids: list[str] = []
    for entry in libraries:
        if isinstance(entry, dict) and entry.get("id") is not None:
            ids.append(str(entry["id"]))
        elif isinstance(entry, str):
            ids.append(entry)
    return ids


def _letterboxd_resolver(api_key: str) -> Callable[[str, str, str | None], dict[str, str] | None]:
    def resolve(slug: str, title: str, year: str | None = None) -> dict[str, str] | None:
        ids = tmdb_client.resolve_letterboxd_film(
            api_key,
            slug=slug,
            title=title,
            year=year,
        )
        return ids or None

    return resolve


def build_sources(
    session: Session,
    job: Job,
    *,
    log: BoundLogger | None = None,
) -> dict[str, Source]:
    """Instantiate client-backed sources required by the job's source pair."""
    required = job.services_for_pair()
    missing = [name for name in required if not _connection_ok(session, Service(name))]
    if missing:
        raise ValueError(f"Connections not configured: {', '.join(sorted(missing))}")

    tmdb_connection = conn_svc.get_connection(session, Service.TMDB)
    tmdb_secrets = (
        conn_svc.load_secrets(tmdb_connection) if tmdb_connection and tmdb_connection.secret_enc else {}
    )
    tmdb_api_key = str(tmdb_secrets.get("api_key", ""))
    letterboxd_resolver = _letterboxd_resolver(tmdb_api_key) if tmdb_api_key else None
    run_log = log or structlog.get_logger("sync")

    sources: dict[str, Source] = {}

    if "plex" in required:
        plex = conn_svc.get_connection(session, Service.PLEX)
        if plex is None:
            raise ValueError("Plex connection not configured")
        config = plex.public_config()
        secrets = conn_svc.load_secrets(plex)
        sources["plex"] = PlexSource(
            url=str(config.get("url", "")),
            token=str(secrets.get("token", "")),
            library_ids=_plex_library_ids(config),
        )

    if "trakt" in required:
        trakt = conn_svc.get_connection(session, Service.TRAKT)
        if trakt is None:
            raise ValueError("Trakt connection not configured")
        access_token = conn_svc.ensure_trakt_access_token(session, trakt)
        client_id, _ = get_settings().require_trakt_credentials()
        sources["trakt"] = TraktSource(client_id=client_id, access_token=access_token)

    if "letterboxd" in required:
        letterboxd = conn_svc.get_connection(session, Service.LETTERBOXD)
        if letterboxd is None:
            raise ValueError("Letterboxd connection not configured")
        config = letterboxd.public_config()
        secrets = conn_svc.load_secrets(letterboxd)
        sources["letterboxd"] = LetterboxdSource(
            username=str(config.get("username", "")),
            password=str(secrets.get("password", "")),
            resolve_identifiers=letterboxd_resolver,
            log=run_log,
        )

    if (
        job.source_pair.value == "plex_trakt"
        and _connection_ok(session, Service.LETTERBOXD)
        and "letterboxd" not in sources
    ):
        letterboxd = conn_svc.get_connection(session, Service.LETTERBOXD)
        if letterboxd is not None:
            config = letterboxd.public_config()
            secrets = conn_svc.load_secrets(letterboxd)
            sources["letterboxd"] = LetterboxdSource(
                username=str(config.get("username", "")),
                password=str(secrets.get("password", "")),
                resolve_identifiers=letterboxd_resolver,
                log=run_log,
            )

    return sources
