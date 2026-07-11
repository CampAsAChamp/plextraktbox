"""Fernet encryption tests."""

from __future__ import annotations

import pytest
from cryptography.fernet import InvalidToken

from plextraktbox.security import decrypt_secret, encrypt_secret


def test_encrypt_decrypt_round_trip() -> None:
    plaintext = "super-secret-token"
    token = encrypt_secret(plaintext)
    assert token != plaintext
    assert decrypt_secret(token) == plaintext


def test_decrypt_rejects_invalid_token() -> None:
    with pytest.raises(InvalidToken):
        decrypt_secret("not-a-valid-token")
