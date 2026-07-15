"""MediaMatcher tests."""

from plextraktbox.sync.matcher import MediaMatcher
from tests.fakes import episode, movie, show


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


def test_match_shows_by_tmdb() -> None:
    left = show(title="Breaking Bad", tmdb="1396", source="plex")
    right = show(title="Breaking Bad", tmdb="1396", tvdb="81189", source="trakt")
    matcher = MediaMatcher()
    matcher.add(right)
    assert matcher.find(left) == right


def test_movie_does_not_match_show_with_same_id() -> None:
    show_item = show(title="Some Show", tmdb="100", source="trakt")
    movie_item = movie(title="Some Movie", tmdb="100", source="plex")
    matcher = MediaMatcher()
    matcher.add(show_item)
    assert matcher.find(movie_item) is None


def test_match_episodes_by_show_id_and_season_episode() -> None:
    left = episode(title="Breaking Bad", season=1, episode=1, tmdb="1396", source="plex")
    right = episode(title="Breaking Bad", season=1, episode=1, tmdb="1396", source="trakt")
    other = episode(title="Breaking Bad", season=1, episode=2, tmdb="1396", source="trakt")
    matcher = MediaMatcher()
    matcher.add(right)
    matcher.add(other)
    assert matcher.find(left) == right
    assert matcher.find(left).title == "Breaking Bad S01E01"


def test_episode_match_key_includes_season_episode() -> None:
    item = episode(title="Show", season=2, episode=5, tmdb="42")
    assert item.match_key() == "tmdb:42:s2e5"
