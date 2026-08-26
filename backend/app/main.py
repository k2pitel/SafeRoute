"""SafeRoute backend — FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import crime_index, incidents, news, reports, routes, segments, zones

app = FastAPI(
    title="SafeRoute API",
    description="Safety-aware pedestrian navigation backend.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents.router)
app.include_router(routes.router)
app.include_router(reports.router)
app.include_router(crime_index.router)
app.include_router(news.router)
app.include_router(segments.router)
app.include_router(zones.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
