from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = Field(default="Cycling Coach Bot", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_data_dir: str = Field(default="data", alias="APP_DATA_DIR")
    app_secret_key: str = Field(default="change-me", alias="APP_SECRET_KEY")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_webhook_secret: str = Field(default="", alias="TELEGRAM_WEBHOOK_SECRET")
    default_strava_athlete_id: int | None = Field(default=None, alias="DEFAULT_STRAVA_ATHLETE_ID")

    strava_client_id: str = Field(default="", alias="STRAVA_CLIENT_ID")
    strava_client_secret: str = Field(default="", alias="STRAVA_CLIENT_SECRET")
    strava_redirect_uri: str = Field(default="", alias="STRAVA_REDIRECT_URI")
    strava_verify_token: str = Field(default="", alias="STRAVA_VERIFY_TOKEN")
    strava_scopes: str = Field(default="read,activity:read_all", alias="STRAVA_SCOPES")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    database_url: str = Field(default="", alias="DATABASE_URL")
    redis_url: str = Field(default="", alias="REDIS_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
