"""Tests for HTTP access log formatting."""

from plextraktbox.http_access import format_access_log_line, service_from_path


def test_service_from_path_for_connection_routes() -> None:
    assert service_from_path("/api/connections/plex/test") == "PLEX"
    assert service_from_path("/api/connections/trakt/device/start") == "TRAKT"
    assert service_from_path("/api/connections/letterboxd") == "LETTERBOXD"
    assert service_from_path("/api/connections/tmdb/test") == "TMDB"


def test_service_from_path_ignores_non_connection_routes() -> None:
    assert service_from_path("/api/setup/status") is None
    assert service_from_path("/api/auth/me") is None
    assert service_from_path("/api/connections/status") is None


def test_format_access_log_line_with_service() -> None:
    assert (
        format_access_log_line("POST", "/api/connections/plex/test", service="PLEX", status_code=200)
        == "POST PLEX /api/connections/plex/test 200"
    )


def test_format_access_log_line_without_service() -> None:
    assert (
        format_access_log_line("GET", "/api/setup/status", status_code=200)
        == "GET /api/setup/status 200"
    )
