"""Local SQLite store for user accounts and community reports.

Deliberately plain SQLite rather than the Postgres/PostGIS models in
datalag/models.py — same reasoning as datalag/news_archive.py: those require
Docker, which this dev setup doesn't run, and accounts/reports here don't
need PostGIS or concurrent-write features to work.
"""
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime

from app.config import settings

DB_PATH = settings.data_dir / "local_store.db"


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                occurred_at TEXT NOT NULL,
                confirmations INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        # One row per (report, confirming user): the primary key is what stops
        # one user from confirming the same report twice (F3).
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS report_confirmations (
                report_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (report_id, user_id)
            )
            """
        )


def create_user(email: str, password_hash: str) -> dict:
    user_id = str(uuid.uuid4())
    created_at = datetime.now(UTC).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, email, password_hash, created_at),
        )
    return {"id": user_id, "email": email, "password_hash": password_hash, "created_at": created_at}


def get_user_by_email(email: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


# report: an object with .type, .description, .latitude, .longitude, .occurred_at
# (a schemas.ReportCreate) — kept as a loose param rather than importing the
# Pydantic schema here to avoid a schemas <-> local_store import cycle.
def create_report(user_id: str, report) -> dict:
    occurred_at = (report.occurred_at or datetime.now(UTC)).isoformat()
    created_at = datetime.now(UTC).isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO reports (user_id, type, description, latitude, longitude, occurred_at, confirmations, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (user_id, report.type, report.description, report.latitude, report.longitude, occurred_at, created_at),
        )
        report_id = cursor.lastrowid
    return get_report(report_id)


def get_report(report_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    return dict(row) if row else None


def list_reports(min_lon: float, min_lat: float, max_lon: float, max_lat: float, limit: int = 200) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM reports
            WHERE longitude BETWEEN ? AND ? AND latitude BETWEEN ? AND ?
            ORDER BY created_at DESC LIMIT ?
            """,
            (min_lon, max_lon, min_lat, max_lat, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def add_confirmation(report_id: int, user_id: str) -> bool:
    """Record ``user_id`` confirming the report and bump its counter, atomically.
    Returns False (and changes nothing) if that user already confirmed it."""
    with _connect() as conn:
        try:
            conn.execute(
                "INSERT INTO report_confirmations (report_id, user_id, created_at) VALUES (?, ?, ?)",
                (report_id, user_id, datetime.now(UTC).isoformat()),
            )
        except sqlite3.IntegrityError:
            return False
        conn.execute("UPDATE reports SET confirmations = confirmations + 1 WHERE id = ?", (report_id,))
    return True


def count_reports_by_user_since(user_id: str, since: datetime) -> int:
    """How many reports ``user_id`` has submitted since ``since`` (NF10).
    ISO 8601 strings in one timezone compare correctly as text."""
    with _connect() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM reports WHERE user_id = ? AND created_at >= ?",
            (user_id, since.astimezone(UTC).isoformat()),
        ).fetchone()[0]
