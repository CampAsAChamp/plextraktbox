"""Build sync sources from configured connections."""

from __future__ import annotations

from sqlmodel import Session

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


def build_sources(session: Session, job: Job) -> dict[str, Source]:
    """Instantiate sources required by the job's source pair.

    Phase 3 uses in-memory adapters; client-backed fetch lands in Phase 7; apply in Phase 8.
    """
    required = job.services_for_pair()
    missing = [name for name in required if not _connection_ok(session, Service(name))]
    if missing:
        raise ValueError(f"Connections not configured: {', '.join(sorted(missing))}")

    sources: dict[str, Source] = {}
    if "plex" in required:
        sources["plex"] = PlexSource()
    if "trakt" in required:
        sources["trakt"] = TraktSource()
    if "letterboxd" in required:
        sources["letterboxd"] = LetterboxdSource()

    # Letterboxd watchlist is read-only input for plex_trakt watchlist jobs.
    if (
        job.source_pair.value == "plex_trakt"
        and _connection_ok(session, Service.LETTERBOXD)
        and "letterboxd" not in sources
    ):
        sources["letterboxd"] = LetterboxdSource()

    return sources
