"""One router per context, registered by main.create_app (tabel 4.1)."""
from app.api.auth.router import router as auth_router
from app.api.crime_index.router import router as crime_index_router
from app.api.incidents.router import router as incidents_router
from app.api.news.router import router as news_router
from app.api.reports.router import router as reports_router
from app.api.routes.router import router as routes_router
from app.api.segments.router import router as segments_router
from app.api.zones.router import router as zones_router

ALL_ROUTERS = [
    auth_router,
    incidents_router,
    routes_router,
    reports_router,
    crime_index_router,
    news_router,
    segments_router,
    zones_router,
]
