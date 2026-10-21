"""Datalag — the persistence subsystem (figur 4.2).

Every other subsystem reaches stored data only through the modules in this
package, so no router or service knows about SQL or file locations:

- ``local_store``  — users + community reports (SQLite, dev-time stand-in)
- ``news_archive`` — append-only crime-news archive (SQLite)
- ``zone_cache``   — municipality zone polygons + scores (in memory)
- ``models`` / ``database`` / ``migrations`` — the PostgreSQL/PostGIS target
  schema (afsnit 4.3.3) and its Alembic migrations
"""
from app.config import settings
from app.datalag import local_store, news_archive


def init_db() -> None:
    """Create the dev-time SQLite tables (idempotent). Called on startup."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    local_store.init_db()
    news_archive.init_db()
