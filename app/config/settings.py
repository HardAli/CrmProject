from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    database_url: str = Field(alias="DATABASE_URL")
    reminder_daily_summary_hour_utc: int = Field(default=7, alias="REMINDER_DAILY_SUMMARY_HOUR_UTC")
    reminder_check_interval_minutes: int = Field(default=15, alias="REMINDER_CHECK_INTERVAL_MINUTES")
    reminder_task_horizon_minutes: int = Field(default=30, alias="REMINDER_TASK_HORIZON_MINUTES")
    supervisor_secret: str = Field(default="HardAdmin31415926535", alias="SUPERVISOR_SECRET")
    role_pass_expire_minutes: int = Field(default=60, alias="ROLE_PASS_EXPIRE_MINUTES")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()