"""GET /api/pipeline/status — how fresh the data is and whether the jobs run (DP-07)."""
from fastapi import APIRouter

from app.datalag import news_archive, world_safety_cache, zone_cache
from app.worker import status

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.get("/status")
def pipeline_status():
    """Per job: last success, last error, stale after two missed runs. Per
    dataset: which period it covers, so the app can say "Data from …"."""
    info = zone_cache.get_info()
    latest = news_archive.load_items(limit=1)
    return {
        "jobs": status.snapshot(),
        "datasets": {
            "crime_statistics": {
                "source": "Danmarks Statistik (STRAF11, FOLK1A)",
                "period": info.crime_period if info else None,
                "population_period": info.population_period if info else None,
                "fetched_at": info.fetched_at if info else None,
                "municipality_polygons": len(zone_cache.get_all()),
            },
            "world_safety": {
                "source": "Eurostat (urb_percep, ilc_mddw03) + World Bank (VC.IHR.PSRC.P5)",
                "countries": len(world_safety_cache.get().countries),
                "cities": len(world_safety_cache.get().cities),
                "fetched_at": world_safety_cache.get().fetched_at,
            },
            "news": {
                "source": "Danish RSS feeds + Internet Archive backfill",
                "archived": news_archive.count(),
                "newest_published_at": latest[0].published_at if latest else None,
            },
        },
    }
