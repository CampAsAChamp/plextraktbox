"""Key/value application settings stored in SQLite."""

from __future__ import annotations

from sqlmodel import Field, SQLModel


class Setting(SQLModel, table=True):
    key: str = Field(primary_key=True, max_length=64)
    value_json: str = Field(default="null")
