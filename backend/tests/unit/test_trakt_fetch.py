"""Trakt fetch client tests (respx)."""

from __future__ import annotations

import respx
from httpx import Response

from plextraktbox.clients import trakt_client


@respx.mock
def test_fetch_watchlist_movies_maps_items() -> None:
    respx.get("https://api.trakt.tv/sync/watchlist").mock(
        return_value=Response(
            200,
            json=[
                {
                    "listed_at": "2024-01-01T00:00:00.000Z",
                    "type": "movie",
                    "movie": {
                        "title": "Parasite",
                        "year": 2019,
                        "ids": {
                            "trakt": 1,
                            "slug": "parasite-2019",
                            "imdb": "tt6751668",
                            "tmdb": 496243,
                        },
                    },
                }
            ],
        )
    )

    items = trakt_client.fetch_watchlist_movies("client-id", "access-token")
    assert len(items) == 1
    assert items[0].title == "Parasite"
    assert items[0].watchlisted is True
    assert items[0].identifiers["tmdb"] == "496243"
