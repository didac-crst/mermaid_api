from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_CODE_LENGTH = 100 * 1024
THEMES = {"default", "neutral", "dark", "forest", "base"}
FORMATS = {"svg", "png", "jpg", "jpeg"}


class ValidateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=False)

    code: str = Field(min_length=1, max_length=MAX_CODE_LENGTH)


class RenderRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=False)

    code: str = Field(min_length=1, max_length=MAX_CODE_LENGTH)
    format: Literal["svg", "png", "jpg", "jpeg"] = "png"
    background: str | None = None
    theme: str = "default"
    width: int = Field(default=1200, ge=100, le=4000)
    height: int = Field(default=800, ge=100, le=4000)
    scale: float = Field(default=1.0, ge=0.5, le=3.0)
    transparent: bool = False

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, theme: str) -> str:
        if theme not in THEMES:
            allowed = ", ".join(sorted(THEMES))
            raise ValueError(f"invalid theme: {theme}. Allowed themes: {allowed}")
        return theme

    @model_validator(mode="after")
    def resolve_background(self) -> "RenderRequest":
        if self.background:
            if self.format in {"jpg", "jpeg"} and self.background.lower() == "transparent":
                self.background = "white"
            return self

        if self.format in {"jpg", "jpeg"}:
            self.background = "white"
        elif self.transparent and self.format in {"png", "svg"}:
            self.background = "transparent"
        else:
            self.background = "white"
        return self
