"""Local archive for crime news items.

RSS only ever exposes each outlet's *current* items — once something
rolls off a feed, it's gone. This module is a tiny append-only store: a
background poller (see main.py's lifespan + routers/news.py) saves every
new item it sees here, so history accumulates for as long as the backend
keeps running, instead of being lost every time a feed rotates.

Deliberately plain SQLite rather than the main Postgres `database.py` —
that requires infrastructure (Docker) this dev setup doesn't have running,
and this archive doesn't need PostGIS/concurrent-write features anyway.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.schemas import NewsItem

DB_PATH = Path(__file__).resolve().parent.parent / "news_archive.db"


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS news_items (
                url TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                published_at TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                archived_at TEXT NOT NULL
            )
            """
        )


def save_items(items: list[NewsItem]) -> int:
    """Insert items not already archived (by URL). Returns how many were new."""
    new_count = 0
    with _connect() as conn:
        for item in items:
            try:
                conn.execute(
                    """
                    INSERT INTO news_items (url, title, source, published_at, latitude, longitude, archived_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.url,
                        item.title,
                        item.source,
                        item.published_at.isoformat(),
                        item.latitude,
                        item.longitude,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                new_count += 1
            except sqlite3.IntegrityError:
                pass  # already archived — feeds re-serve the same items on every poll
    return new_count


def load_items(city_filter: str | None = None, limit: int = 500, year: int | None = None) -> list[NewsItem]:
    """
    year: restricts to that calendar year (ISO date strings sort/compare
    correctly as plain text, so a "YYYY-01-01" .. "YYYY-12-31" range works
    without parsing every row). Without it, this is "most recent N" — with
    thousands of items now archived (see news_backfill.py), the live/recent
    ones would otherwise always crowd out everything from 2020-2025.
    """
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        if year is not None:
            rows = conn.execute(
                "SELECT * FROM news_items WHERE published_at >= ? AND published_at < ? ORDER BY published_at DESC LIMIT ?",
                (f"{year}-01-01", f"{year + 1}-01-01", limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM news_items ORDER BY published_at DESC LIMIT ?", (limit,)
            ).fetchall()

    items = []
    for row in rows:
        if city_filter and city_filter not in row["title"].lower():
            continue
        items.append(
            NewsItem(
                title=row["title"],
                url=row["url"],
                source=row["source"],
                published_at=datetime.fromisoformat(row["published_at"]),
                latitude=row["latitude"],
                longitude=row["longitude"],
            )
        )
    return items


def count() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM news_items").fetchone()[0]
