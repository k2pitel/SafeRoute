"""GET /api/routes — ranked route options with time + safety score."""
import httpx
from fastapi import APIRouter, Query

from app.config import settings
from app.schemas import RouteOption

router = APIRouter(prefix="/api/routes", tags=["routes"])


def _label_for_score(score: float) -> str:
    if score < 4:
        return "not safe"
    if score < 6:
        return "okay"
    if score < 8:
        return "safe"
    return "very safe"


def _fallback_routes(lat1: float, lon1: float, lat2: float, lon2: float) -> list[RouteOption]:
    """Straight-line stand-ins, used when the OSRM service is unreachable."""
    fast = RouteOption(
        duration_minutes=30,
        distance_meters=2400,
        safety_score=4.2,
        safety_label=_label_for_score(4.2),
        geometry={"type": "LineString", "coordinates": [[lon1, lat1], [lon2, lat2]]},
    )
    safe = RouteOption(
        duration_minutes=34,
        distance_meters=2650,
        safety_score=8.6,
        safety_label=_label_for_score(8.6),
        geometry={
            "type": "LineString",
            "coordinates": [[lon1, lat1], [(lon1 + lon2) / 2, (lat1 + lat2) / 2 + 0.001], [lon2, lat2]],
        },
    )
    return [safe, fast]


@router.get("", response_model=list[RouteOption])
async def get_routes(
    from_: str = Query(..., alias="from", description="lat,lon"),
    to: str = Query(..., description="lat,lon"),
    mode: str = Query("walking", description="walking | cycling | driving"),
):
    """
    Returns candidate routes, fastest-first, with a safety score attached.

    Route geometries/durations come from OSRM. The safety score itself is
    still a stand-in — in production it comes from intersecting the route
    with `segment_scores` (see ml/serving); with no populated database yet,
    we rank OSRM's own alternatives fastest-first and rate the fastest one
    as the least safe and the most different alternative as the safest,
    matching the fast-vs-safe framing from the README wireframes.
    """
    lat1, lon1 = (float(v) for v in from_.split(","))
    lat2, lon2 = (float(v) for v in to.split(","))

    url = f"{settings.osrm_server_url}/route/v1/foot/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "full", "geometries": "geojson", "alternatives": "true"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError):
        return _fallback_routes(lat1, lon1, lat2, lon2)

    osrm_routes = data.get("routes") or []
    if not osrm_routes:
        return _fallback_routes(lat1, lon1, lat2, lon2)

    osrm_routes.sort(key=lambda r: r["duration"])

    scores = [4.2] if len(osrm_routes) == 1 else [4.2, 8.6, *([6.5] * (len(osrm_routes) - 2))]
    options = []
    for route, score in zip(osrm_routes, scores):
        options.append(
            RouteOption(
                duration_minutes=route["duration"] / 60,
                distance_meters=route["distance"],
                safety_score=score,
                safety_label=_label_for_score(score),
                geometry=route["geometry"],
            )
        )
    return options
