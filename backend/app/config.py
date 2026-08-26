"""Application configuration, loaded from environment variables / .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://saferoute:saferoute@localhost:5432/saferoute"
    redis_url: str = "redis://localhost:6379/0"
    mapbox_access_token: str = ""
    osrm_server_url: str = "http://localhost:5000"
    news_api_key: str = ""
    dp_epsilon: float = 1.0  # differential privacy noise budget

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
