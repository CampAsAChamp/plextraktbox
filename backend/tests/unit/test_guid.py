"""GUID parsing tests."""

from plextraktbox.sync.guid import identifiers_from_guids, letterboxd_slug, parse_guid


def test_parse_tmdb_guid() -> None:
    parsed = parse_guid("tmdb://603")
    assert parsed is not None
    assert parsed.scheme == "tmdb"
    assert parsed.value == "603"


def test_identifiers_from_guids() -> None:
    ids = identifiers_from_guids(["tmdb://603", "imdb://tt0133093"])
    assert ids == {"tmdb": "603", "imdb": "tt0133093"}


def test_letterboxd_slug() -> None:
    assert letterboxd_slug("https://letterboxd.com/film/the-matrix/") == "the-matrix"
