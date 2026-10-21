"""Picks the Async Worker realisation from configuration (settings.async_worker)."""
from app.worker.base import AsyncWorker


def create_async_worker(kind: str) -> AsyncWorker:
    if kind == "background":
        from app.worker.background import BackgroundAsyncWorker

        return BackgroundAsyncWorker()
    if kind == "celery":
        from app.worker.celery_worker import CeleryAsyncWorker

        return CeleryAsyncWorker()
    raise ValueError(f"unknown async worker: {kind!r}")
