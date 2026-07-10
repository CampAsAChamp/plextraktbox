"""Local user account (single-user app)."""

from __future__ import annotations

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=64)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
