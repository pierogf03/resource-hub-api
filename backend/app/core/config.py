from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")




    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/resource_hub"
    JWT_SECRET_KEY: str = "change_me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    APP_NAME: str = "Resource Hub"
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:4200"

    WORKATO_AI_CHAT_URL: str = ""
    WORKATO_AI_CHAT_API_KEY: str = ""
    WORKATO_INTERNAL_API_KEY: str = ""
    AI_CHAT_ENABLED: bool = True
    AI_CHAT_AUDIT_ENABLED: bool = True
    AI_CHAT_TIMEOUT_SECONDS: int = 60
    AI_CHAT_MAX_MESSAGE_LENGTH: int = 4000

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
