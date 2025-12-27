# src/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "mini-rag"
    APP_VERSION: str = "0.1.0"
    ENV: str = "local"

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Optional: LLM/Embeddings keys (later)
    OPENAI_API_KEY: str | None = None
    HF_TOKEN: str | None = None

    # Load .env automatically
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings loader.
    - Reads from environment variables + .env
    - Cached so it's created once per process
    """
    return Settings()
