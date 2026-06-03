"""Type-safe configuration loaded from .env via pydantic-settings."""
from __future__ import annotations

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admins: Annotated[list[int], NoDecode] = []
    use_redis: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("admins", mode="before")
    @classmethod
    def _parse_admins(cls, value: object) -> object:
        """Accept ADMINS=123,456 comma-separated format."""
        if isinstance(value, str):
            return [int(part) for part in value.replace(" ", "").split(",") if part]
        return value


settings = Settings()
