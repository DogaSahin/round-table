# backend/app/core/config.py
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, env-driven config. Fails fast (pydantic raises on construction)
    on a malformed value rather than crashing lazily at first use."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./data/roundtable.db"
    media_dir: Path = Path("./data/media")
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    enabled_modules: Annotated[list[str], NoDecode] = ["app.modules.dice"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("enabled_modules", mode="before")
    @classmethod
    def _split_modules_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [name.strip() for name in value.split(",") if name.strip()]
        return value

    def model_post_init(self, __context: object) -> None:
        self.media_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
