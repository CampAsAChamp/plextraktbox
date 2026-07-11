"""Gravatar URL helper tests."""

from __future__ import annotations

from plextraktbox.utils.gravatar import gravatar_url


def test_gravatar_url_normalizes_email() -> None:
    assert gravatar_url("  Nick@Example.COM ") == gravatar_url("nick@example.com")


def test_gravatar_url_known_hash() -> None:
    assert (
        gravatar_url("nick@example.com")
        == "https://www.gravatar.com/avatar/484f70e21a3d3480e013519f8236bb86?s=80&d=identicon"
    )
