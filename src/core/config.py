from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    SESSION_COOKIE_NAME: str = "session_id"
    SESSION_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7

    COOKIE_SECURE: bool = True
    COOKIE_HTTP_ONLY: bool = True
    COOKIE_SAME_SITE: str = "lax"

    REDIS_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()