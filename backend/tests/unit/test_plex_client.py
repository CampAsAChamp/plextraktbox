"""Plex client unit tests."""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import respx

from plextraktbox.clients import plex_client

PLEX_IDENTITY_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<MediaContainer friendlyName="Home Plex" machineIdentifier="abc123"/>'
)


def test_plex_server_ssl_verify_for_direct_urls() -> None:
    assert plex_client.plex_server_ssl_verify("https://10-0-0-25.abc.plex.direct:32400") is False
    assert plex_client.plex_server_ssl_verify("http://192.168.1.10:32400") is True
    assert plex_client.plex_server_ssl_verify("https://plex.example.com:32400") is True


@respx.mock
def test_list_libraries_reads_sections_xml() -> None:
    respx.get("https://10-0-0-25.abc.plex.direct:32400/library/sections").mock(
        return_value=httpx.Response(
            200,
            text=(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<MediaContainer size="2">'
                '<Directory key="1" type="movie" title="Movies"/>'
                '<Directory key="2" type="show" title="TV Shows"/>'
                "</MediaContainer>"
            ),
        )
    )

    libraries = plex_client.list_libraries(
        "https://10-0-0-25.abc.plex.direct:32400",
        "plex-token",
    )

    assert len(libraries) == 2
    assert libraries[0].id == "1"
    assert libraries[0].title == "Movies"
    assert libraries[0].library_type == "movie"
    assert libraries[1].id == "2"
    assert libraries[1].title == "TV Shows"
    assert libraries[1].library_type == "show"


@respx.mock
def test_list_libraries_sorts_alphabetically() -> None:
    respx.get("http://plex.local:32400/library/sections").mock(
        return_value=httpx.Response(
            200,
            text=(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<MediaContainer size="3">'
                '<Directory key="3" type="movie" title="Z Movies"/>'
                '<Directory key="1" type="movie" title="Alpha"/>'
                '<Directory key="2" type="movie" title="beta"/>'
                "</MediaContainer>"
            ),
        )
    )

    libraries = plex_client.list_libraries("http://plex.local:32400", "plex-token")

    assert [library.title for library in libraries] == ["Alpha", "beta", "Z Movies"]


@respx.mock
def test_list_libraries_raises_value_error_on_connect_failure() -> None:
    respx.get("http://plex.local:32400/library/sections").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    try:
        plex_client.list_libraries("http://plex.local:32400", "plex-token")
    except ValueError as exc:
        assert "Plex library list failed" in str(exc)
    else:
        raise AssertionError("expected ValueError")


@respx.mock
def test_find_connectable_server_tries_fallback_urls() -> None:
    calls: list[str] = []

    def identity_handler(request: httpx.Request) -> httpx.Response:
        base = str(request.url).split("?")[0].removesuffix("/identity")
        calls.append(base)
        if "plex.direct" in base:
            return httpx.Response(503, text="relay unreachable")
        return httpx.Response(200, text=PLEX_IDENTITY_XML)

    respx.get(url__regex=r"https?://.*/identity").mock(side_effect=identity_handler)
    respx.get("https://plex.tv/api/v2/resources").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "name": "Home Plex",
                    "product": "Plex Media Server",
                    "provides": "server",
                    "owned": True,
                    "clientIdentifier": "abc123",
                    "accessToken": "server-token",
                    "connections": [
                        {
                            "uri": "http://192.168.1.10:32400",
                            "local": True,
                            "relay": False,
                            "protocol": "http",
                        },
                        {
                            "uri": "https://10-0-0-25.abc.plex.direct:32400",
                            "local": False,
                            "relay": True,
                            "protocol": "https",
                        },
                    ],
                }
            ],
        )
    )

    server, result = plex_client.find_connectable_server("account-token", "client-id")

    assert server is not None
    assert result is not None
    assert result.ok is True
    assert server.url == "http://192.168.1.10:32400"
    assert calls[0].endswith(".plex.direct:32400")
    assert "http://192.168.1.10:32400" in calls
    assert calls.index("http://192.168.1.10:32400") > 0


@respx.mock
def test_test_connection_reads_identity_xml() -> None:
    respx.get("http://plex.local:32400/identity").mock(
        return_value=httpx.Response(200, text=PLEX_IDENTITY_XML)
    )

    result = plex_client.test_connection("http://plex.local:32400", "plex-token")

    assert result.ok is True
    assert result.details == {"friendly_name": "Home Plex", "machine_id": "abc123"}


def test_fetch_ratings_movies_includes_unrated_library_items(monkeypatch) -> None:
    rated = SimpleNamespace(
        type="movie",
        title="Rated Film",
        ratingKey="1",
        guid="tmdb://603",
        guids=[],
        userRating=8.0,
        viewCount=1,
        lastViewedAt=None,
    )
    unrated = SimpleNamespace(
        type="movie",
        title="Unrated Film",
        ratingKey="2",
        guid="tmdb://949",
        guids=[],
        userRating=None,
        viewCount=0,
        lastViewedAt=None,
    )
    monkeypatch.setattr(
        plex_client,
        "fetch_library_movies",
        lambda *_args, **_kwargs: [rated, unrated],
    )

    items = plex_client.fetch_ratings_movies("http://plex.local:32400", "plex-token")

    assert len(items) == 2
    assert items[0].title == "Rated Film"
    assert items[0].rating == 8.0
    assert items[1].title == "Unrated Film"
    assert items[1].rating is None
