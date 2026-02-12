from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CHAiNALYZE"
    environment: str = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8001

    postgres_dsn: str = "postgresql+asyncpg://chainalyze:chainalyze@db:5432/chainalyze"
    postgres_sync_dsn: str = "postgresql://chainalyze:chainalyze@db:5432/chainalyze"
    redis_url: str = "redis://redis:6379/0"

    exchange_name: str = "binance"
    symbols: str = "BTC/USDT,ETH/USDT"
    timeframes: str = "1m,5m,1h"

    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
