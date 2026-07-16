"""Plex server connection test, PIN-based account linking, and library fetch.

Thin facade re-exporting ``plex_auth``, ``plex_library``, and ``plex_apply`` so
existing ``from plextraktbox.clients import plex_client`` imports keep working.
"""

from __future__ import annotations

from plextraktbox.clients import plex_apply, plex_auth, plex_library

# Auth
PLEX_PINS_URL = plex_auth.PLEX_PINS_URL
PLEX_RESOURCES_URL = plex_auth.PLEX_RESOURCES_URL
PLEX_LINK_URL = plex_auth.PLEX_LINK_URL
PLEX_PRODUCT = plex_auth.PLEX_PRODUCT
PLEX_VERSION = plex_auth.PLEX_VERSION
PIN_EXPIRES_IN = plex_auth.PIN_EXPIRES_IN
PIN_POLL_INTERVAL = plex_auth.PIN_POLL_INTERVAL
PlexPinStart = plex_auth.PlexPinStart
PlexDiscoveredServer = plex_auth.PlexDiscoveredServer
plex_server_ssl_verify = plex_auth.plex_server_ssl_verify
plex_client_identifier = plex_auth.plex_client_identifier
_plex_headers = plex_auth._plex_headers
_build_auth_url = plex_auth._build_auth_url
start_pin_flow = plex_auth.start_pin_flow
poll_pin_token = plex_auth.poll_pin_token
_rank_connection_urls = plex_auth._rank_connection_urls
discover_servers = plex_auth.discover_servers
find_connectable_server = plex_auth.find_connectable_server
pick_best_server = plex_auth.pick_best_server
test_connection = plex_auth.test_connection

# Library
PlexLibrarySnapshot = plex_library.PlexLibrarySnapshot
PlexLibraryInfo = plex_library.PlexLibraryInfo
_index_videos_by_match_key = plex_library._index_videos_by_match_key
_index_episodes_by_match_key = plex_library._index_episodes_by_match_key
_plex_server = plex_library._plex_server
list_libraries = plex_library.list_libraries
fetch_watchlist_movies = plex_library.fetch_watchlist_movies
fetch_watchlist = plex_library.fetch_watchlist
fetch_library_movies = plex_library.fetch_library_movies
fetch_library_shows = plex_library.fetch_library_shows
_fetch_library_entries = plex_library._fetch_library_entries
fetch_library_episodes = plex_library.fetch_library_episodes
fetch_ratings_movies = plex_library.fetch_ratings_movies
fetch_watched_movies = plex_library.fetch_watched_movies
fetch_watched = plex_library.fetch_watched
_library_videos_by_match_key = plex_library._library_videos_by_match_key
_library_episodes_by_match_key = plex_library._library_episodes_by_match_key
_find_library_video = plex_library._find_library_video

# Apply
PLEX_DISCOVER_BASE = plex_apply.PLEX_DISCOVER_BASE
PLEX_DISCOVER_IDENTIFIER = plex_apply.PLEX_DISCOVER_IDENTIFIER
rate_library_movies = plex_apply.rate_library_movies
_discover_metadata_key = plex_apply._discover_metadata_key
rate_discover_movie = plex_apply.rate_discover_movie
rate_discover_movie_by_key = plex_apply.rate_discover_movie_by_key
rate_movies_with_discover_fallback = plex_apply.rate_movies_with_discover_fallback
mark_library_movies_watched = plex_apply.mark_library_movies_watched
mark_library_items_watched = plex_apply.mark_library_items_watched
_plex_account = plex_apply._plex_account
_resolve_discover_item = plex_apply._resolve_discover_item
_resolve_discover_movie = plex_apply._resolve_discover_movie
_find_watchlist_entry = plex_apply._find_watchlist_entry
add_watchlist_movies = plex_apply.add_watchlist_movies
add_watchlist_items = plex_apply.add_watchlist_items
remove_watchlist_movies = plex_apply.remove_watchlist_movies
remove_watchlist_items = plex_apply.remove_watchlist_items

__all__ = [
    "PLEX_DISCOVER_BASE",
    "PLEX_DISCOVER_IDENTIFIER",
    "PLEX_LINK_URL",
    "PLEX_PINS_URL",
    "PLEX_PRODUCT",
    "PLEX_RESOURCES_URL",
    "PLEX_VERSION",
    "PIN_EXPIRES_IN",
    "PIN_POLL_INTERVAL",
    "PlexDiscoveredServer",
    "PlexLibraryInfo",
    "PlexLibrarySnapshot",
    "PlexPinStart",
    "_build_auth_url",
    "_discover_metadata_key",
    "_fetch_library_entries",
    "_find_library_video",
    "_find_watchlist_entry",
    "_index_episodes_by_match_key",
    "_index_videos_by_match_key",
    "_library_episodes_by_match_key",
    "_library_videos_by_match_key",
    "_plex_account",
    "_plex_headers",
    "_plex_server",
    "_rank_connection_urls",
    "_resolve_discover_item",
    "_resolve_discover_movie",
    "add_watchlist_items",
    "add_watchlist_movies",
    "discover_servers",
    "fetch_library_episodes",
    "fetch_library_movies",
    "fetch_library_shows",
    "fetch_ratings_movies",
    "fetch_watched",
    "fetch_watched_movies",
    "fetch_watchlist",
    "fetch_watchlist_movies",
    "find_connectable_server",
    "list_libraries",
    "mark_library_items_watched",
    "mark_library_movies_watched",
    "pick_best_server",
    "plex_client_identifier",
    "plex_server_ssl_verify",
    "poll_pin_token",
    "rate_discover_movie",
    "rate_discover_movie_by_key",
    "rate_library_movies",
    "rate_movies_with_discover_fallback",
    "remove_watchlist_items",
    "remove_watchlist_movies",
    "start_pin_flow",
    "test_connection",
]
