# src/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    # App
    APP_NAME: str = "mini-rag"
    APP_VERSION: str = "0.1.0"
    ENV: str = "local"

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Security / Keys
    OPENAI_API_KEY: str | None = None
    HF_TOKEN: str | None = None

    # Upload rules
    FILE_ALLOWED_TYPES: list[str] = ["text/plain", "application/pdf"]
    FILE_MAX_SIZE: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("FILE_ALLOWED_TYPES", mode="before")
    @classmethod
    def parse_allowed_types(cls, v):
        # Accept:
        # - "text/plain,application/pdf"
        # - ["text/plain","application/pdf"]
        if v is None:
            return ["text/plain", "application/pdf"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
