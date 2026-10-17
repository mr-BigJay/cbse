from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://ardm:ardm@localhost:5432/ardm"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    command_hmac_secret: str = "command-hmac-secret"
    command_default_ttl_seconds: int = 900
    enrollment_code_ttl_minutes: int = 60
    location_retention_days: int = 30
    cors_origins: str = "http://localhost:3000"
    admin_email: str = "admin@localhost"
    admin_password: str = "changeme"
    rate_limit: str = "60/minute"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
