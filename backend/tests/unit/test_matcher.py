"""MediaMatcher tests."""

from plextraktbox.sync.matcher import MediaMatcher
from tests.fakes import movie


def test_match_by_tmdb() -> None:
    left = movie(title="The Matrix", tmdb="603", source="plex")
    right = movie(title="Matrix", tmdb="603", imdb="tt0133093", source="trakt")
    matcher = MediaMatcher()
    assert matcher.find(left) is None
    matcher.add(right)
    assert matcher.find(left) == right


def test_match_pairs() -> None:
    plex_items = [
        movie(title="A", tmdb="1", source="plex"),
        movie(title="B", tmdb="2", source="plex"),
    ]
    trakt_items = [
        movie(title="A alt", tmdb="1", source="trakt"),
        movie(title="C", tmdb="3", source="trakt"),
    ]
    matcher = MediaMatcher()
    pairs = matcher.match_pairs(plex_items, trakt_items)
    assert len(pairs) == 1
    assert pairs[0][0].title == "A"
    assert pairs[0][1].title == "A alt"
