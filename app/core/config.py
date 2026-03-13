from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Mock MCP Server"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    api_key_header: str = "X-Api-Key"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
