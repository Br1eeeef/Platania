from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Platania API"
    environment: str = Field("development", validation_alias="PLATANIA_ENV")
    data_mode: Literal["auto", "live", "demo"] = Field("auto", validation_alias="PLATANIA_DATA_MODE")
    cache_dir: Path = Field(ROOT_DIR / "data" / "cache", validation_alias="PLATANIA_CACHE_DIR")
    cache_ttl_hours: int = Field(24, ge=1, le=168, validation_alias="PLATANIA_CACHE_TTL_HOURS")
    cors_origins_raw: str = Field("http://localhost:5173", validation_alias="PLATANIA_CORS_ORIGINS")
    log_level: str = Field("INFO", validation_alias="PLATANIA_LOG_LEVEL")
    public_url: str = Field("http://localhost:5173", validation_alias="PLATANIA_PUBLIC_URL")
    admin_user_ids_raw: str = Field("", validation_alias="PLATANIA_ADMIN_USER_IDS")
    provider_min_interval_seconds: float = Field(1.5, ge=0.5, validation_alias="PLATANIA_PROVIDER_MIN_INTERVAL_SECONDS")
    provider_timeout_seconds: float = Field(20, ge=3, le=120, validation_alias="PLATANIA_PROVIDER_TIMEOUT_SECONDS")
    provider_max_retries: int = Field(3, ge=1, le=6, validation_alias="PLATANIA_PROVIDER_MAX_RETRIES")

    deepseek_api_key: str = Field("", validation_alias="DEEPSEEK_API_KEY")
    deepseek_api_base: str = Field("https://api.deepseek.com", validation_alias="DEEPSEEK_API_BASE")
    deepseek_model: str = Field("deepseek-chat", validation_alias="DEEPSEEK_MODEL")
    deepseek_daily_free_limit: int = Field(3, ge=1, le=100, validation_alias="DEEPSEEK_DAILY_FREE_LIMIT")

    supabase_url: str = Field("", validation_alias="SUPABASE_URL")
    supabase_secret_key: str = Field(
        "",
        validation_alias=AliasChoices("SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY"),
    )
    supabase_jwt_secret: str = Field("", validation_alias="SUPABASE_JWT_SECRET")

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins_raw.split(",") if value.strip()]

    @property
    def demo_mode(self) -> bool:
        return self.data_mode == "demo"

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_jwt_secret and self.supabase_secret_key)

    @property
    def deepseek_enabled(self) -> bool:
        return bool(self.deepseek_api_key)

    @property
    def admin_user_ids(self) -> set[str]:
        return {value.strip() for value in self.admin_user_ids_raw.split(",") if value.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
