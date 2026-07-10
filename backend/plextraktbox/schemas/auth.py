"""Auth and setup request/response DTOs."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from plextraktbox.models.user import User

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SetupStatusResponse(BaseModel):
    needs_setup: bool


class SetupUserRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not _EMAIL_RE.match(value):
            raise ValueError("Invalid email address")
        return value


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    @classmethod
    def from_user(cls, user: User) -> UserResponse:
        if user.id is None:
            raise ValueError("user has no id")
        return cls(id=user.id, username=user.username, email=user.email)
