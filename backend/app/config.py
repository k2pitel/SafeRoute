"""Application configuration, loaded from environment variables / .env."""
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Where the dev-time SQLite stores live (Datalag). Git-ignored.
    data_dir: Path = BACKEND_DIR / "data"
    database_url: str = "postgresql://saferoute:saferoute@localhost:5432/saferoute"
    redis_url: str = "redis://localhost:6379/0"
    mapbox_access_token: str = ""
    osrm_server_url: str = "http://localhost:5000"
    news_api_key: str = ""
    dp_epsilon: float = 1.0  # differential privacy noise budget (NF11)
    jwt_secret_key: str = "dev-insecure-secret-change-me"  # override via env in real deployments

    # Async Worker realisation (afsnit 4.3 / 4.3.4.5): "background" is the
    # launch variant (asyncio loops inside the Backend API process),
    # "celery" the target architecture (separate Celery worker + Redis).
    async_worker: Literal["background", "celery"] = "background"

    # F3: confirmations needed before a report counts as verified and
    # triggers an event-driven score recalculation (afsnit 4.2.3, NF5).
    report_verification_threshold: int = 3

    # NF10: at most this many reports per user per rolling window (anti-spam).
    report_rate_limit: int = 5
    report_rate_window_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
