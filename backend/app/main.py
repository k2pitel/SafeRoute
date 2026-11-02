"""SafeRoute backend — composition root.

Wires the server-side subsystems from figur 4.2 together: the Backend API
(api/), the Async Worker (worker/) and the Datalag (datalag/). Nothing else
in the code base instantiates subsystems; everything else receives them.

Run locally with:
    uvicorn app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import datalag
from app.api.routers import ALL_ROUTERS
from app.config import settings
from app.worker import AsyncWorker
from app.worker.factory import create_async_worker

DEFAULT_SECRET = "dev-insecure-secret-change-me"


def create_app(async_worker: AsyncWorker | None = None) -> FastAPI:
    worker = async_worker or create_async_worker(settings.async_worker)
    if settings.jwt_secret_key == DEFAULT_SECRET:
        # US-58: fine on a laptop, never on a server. Set JWT_SECRET_KEY in .env.
        logging.getLogger("saferoute").warning(
            "JWT_SECRET_KEY is the built-in dev default; set a real secret before deploying"
        )

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

    # US-58: only the web build sends an Origin header; native apps aren't
    # affected. Allowed origins come from settings (config.py).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Admin-Token"],
    )

    for router in ALL_ROUTERS:
        app.include_router(router)

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
