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
    osrm_server_url: str = "http://localhost:5000"
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

    # NF4/US-16: reports older than this are hidden from the map (still kept
    # for scoring until report_retention_days).
    report_visible_hours: int = 24
    # US-59 (GDPR): reports and confirmations are deleted after this many days.
    report_retention_days: int = 365

    # US-58: login brute-force limit, per email, per rolling window.
    login_max_failures: int = 10
    login_failure_window_minutes: int = 15

    # US-58: CORS. Native apps don't send Origin; this only matters for the
    # web build. Quick tunnels get random names, hence the regex.
    cors_origins: list[str] = ["http://localhost:8081", "http://localhost:19006", "http://localhost:8083"]
    cors_origin_regex: str | None = r"https://[a-z0-9-]+\.(trycloudflare\.com|on\.expo\.app|exp\.direct)"

    # US-58: admin-only endpoints (e.g. POST /api/news/backfill) need this
    # value in the X-Admin-Token header. Unset = those endpoints are disabled.
    admin_token: str | None = None

    # Anchored to backend/ so uvicorn, alembic and scripts read the same file
    # whatever directory they are started from.
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")


settings = Settings()
