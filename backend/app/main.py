"""SafeRoute backend — composition root.

Wires the server-side subsystems from figur 4.2 together: the Backend API
(api/), the Async Worker (worker/) and the Datalag (datalag/). Nothing else
in the code base instantiates subsystems; everything else receives them.

Run locally with:
    uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import datalag
from app.api.routers import ALL_ROUTERS
from app.config import settings
from app.worker import AsyncWorker
from app.worker.factory import create_async_worker


def create_app(async_worker: AsyncWorker | None = None) -> FastAPI:
    worker = async_worker or create_async_worker(settings.async_worker)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        datalag.init_db()
        await worker.start()
        yield
        await worker.stop()

    app = FastAPI(
        title="SafeRoute API",
        description="Safety-aware pedestrian navigation backend.",
        version="0.1.0",
        lifespan=lifespan,
    )
    # Set at construction, not in lifespan, so the API can enqueue work even
    # before the worker starts (queued jobs run once it does).
    app.state.async_worker = worker

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten before production
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in ALL_ROUTERS:
        app.include_router(router)

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
