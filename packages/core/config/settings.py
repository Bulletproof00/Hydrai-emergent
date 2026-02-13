from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CHAiNALYZE"
    environment: str = "dev"

    postgres_dsn: str = "postgresql+asyncpg://chainalyze:chainalyze@db:5432/chainalyze"
    postgres_sync_dsn: str = "postgresql://chainalyze:chainalyze@db:5432/chainalyze"
    redis_url: str = "redis://redis:6379/0"
    chainalyze_master_key: str = "change-me"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
