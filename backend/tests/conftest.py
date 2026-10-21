"""Shared fixtures — isolate tests from the dev SQLite files, the network and the Async Worker."""
import pytest
from fastapi.testclient import TestClient

from app.datalag import local_store, news_archive
from app.main import create_app
from app.worker import AsyncWorker


class RecordingAsyncWorker(AsyncWorker):
    """Test double: records submitted jobs instead of running them."""

    def __init__(self):
        self.recalculations = []

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    def submit_recalculation(self, area) -> None:
        self.recalculations.append(area)


@pytest.fixture
def tmp_stores(tmp_path, monkeypatch):
    """Point both SQLite stores at throwaway files instead of the real dev DBs."""
    monkeypatch.setattr(local_store, "DB_PATH", tmp_path / "local_store.db")
    monkeypatch.setattr(news_archive, "DB_PATH", tmp_path / "news_archive.db")
    local_store.init_db()
    news_archive.init_db()


@pytest.fixture
def async_worker():
    return RecordingAsyncWorker()


@pytest.fixture
def client(tmp_stores, async_worker):
    # Not used as a context manager on purpose: that would run the lifespan,
    # whose real worker polls news/crime stats over the network.
    return TestClient(create_app(async_worker=async_worker))


@pytest.fixture
def new_user(client):
    """Factory: sign up a fresh user, return their Authorization header."""
    count = 0

    def make():
        nonlocal count
        count += 1
        resp = client.post("/api/auth/signup", json={"email": f"user{count}@example.com", "password": "hemmeligt"})
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    return make


@pytest.fixture
def auth_header(new_user):
    return new_user()
