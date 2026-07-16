"""Theme API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ThemeInfoResponse(BaseModel):
    id: str
    name: str
    source: str
    swatches: list[str] | None = None


class ThemeUploadRequest(BaseModel):
    css: str = Field(min_length=1)
    filename: str | None = None


class ThemeUpdateRequest(BaseModel):
    theme_id: str = Field(min_length=1, max_length=63)


class ThemeActiveResponse(BaseModel):
    theme_id: str
