"""GET /api/routes — ranked route options with time + safety score."""
from fastapi import APIRouter, Query

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


@router.get("", response_model=list[RouteOption])
def get_routes(
    from_: str = Query(..., alias="from", description="lat,lon"),
    to: str = Query(..., description="lat,lon"),
    mode: str = Query("walking", description="walking | cycling | driving"),
):
    """
    Returns candidate routes sorted fastest-first.

    NOTE: stub. In production this calls the OSRM /route service for the
    raw geometries/durations, then annotates each with a safety score by
    intersecting the route with `segment_scores` (see ml/serving).
    """
    lat1, lon1 = (float(v) for v in from_.split(","))
    lat2, lon2 = (float(v) for v in to.split(","))

    fast_route = RouteOption(
        duration_minutes=30,
        distance_meters=2400,
        safety_score=4.2,
        safety_label=_label_for_score(4.2),
        geometry={
            "type": "LineString",
            "coordinates": [[lon1, lat1], [lon2, lat2]],
        },
    )
    safe_route = RouteOption(
        duration_minutes=34,
        distance_meters=2650,
        safety_score=8.6,
        safety_label=_label_for_score(8.6),
        geometry={
            "type": "LineString",
            "coordinates": [[lon1, lat1], [(lon1 + lon2) / 2, (lat1 + lat2) / 2 + 0.001], [lon2, lat2]],
        },
    )
    return [safe_route, fast_route]
