"""Password hashing and symmetric encryption of secrets at rest.

Session handling is provided by Starlette's ``SessionMiddleware`` (configured in
``main.py``); this module owns password hashing (bcrypt) and Fernet
encryption/decryption for third-party tokens.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from passlib.context import CryptContext

from plextraktbox.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def _fernet() -> Fernet:
    return Fernet(get_settings().fernet_key)


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret for storage. Returns a urlsafe token string."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    """Decrypt a stored secret. Raises ``InvalidToken`` if the key/data mismatch."""
    return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")


__all__ = [
    "InvalidToken",
    "decrypt_secret",
    "encrypt_secret",
    "hash_password",
    "verify_password",
]
