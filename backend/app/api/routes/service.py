"""Rutetjenesten — Backend API's part of UC1 (F1, NF1, NF7).

Gets route geometries from OSRM (external/osrm.py) and scores each with
the rule-based baseline (worker/scoring/baseline.py, ML-03): the official
crime rate of the areas passed, verified community reports near the route
and the time of day. When segment scores exist (US-30) this is where they
plug in; the RouteOption contract stays the same.

If OSRM fails in any way, ``_fallback_routes`` answers instead, with
times estimated from the straight-line distance (US-10), so the user
always gets a reply (NF7).

NF8: every option carries an explanation built from the same factors the
score used, and says plainly what isn't scored yet (lighting, foot traffic).
"""
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.api.routes.schemas import RouteOption
from app.api.zones import service as zones
from app.config import settings
from app.datalag import local_store
from app.external import osrm
from app.shared.geo import BBox, LatLon, haversine_m, point_to_line_m
from app.worker.scoring import baseline

LOCAL_TZ = ZoneInfo("Europe/Copenhagen")

# US-10: straight-line → realistic estimate. Streets add roughly a third to
# the crow-flies distance in Danish towns; typical speeds per mode.
DETOUR_FACTOR = 1.3
SPEED_M_PER_MIN = {"walking": 5000 / 60, "cycling": 15000 / 60}
REPORT_LOOKBACK = timedelta(days=30)
_ROUTE_BUFFER_DEG = 0.0015  # ≈ 100–170 m around the route's bounding box


class UnsupportedModeError(ValueError):
    pass


def label_for_score(score: float) -> str:
    if score < 4:
        return "not safe"
    if score < 6:
        return "okay"
    if score < 8:
        return "safe"
    return "very safe"


_ZONE_LABEL_TEXT = {
    "unsafe": "well above the national average",
    "mixed": "above the national average",
    "safe": "around or below the national average",
}
_NOT_YET_SCORED = "Street lighting and foot traffic are not scored yet."


def _reports_near(coords: list[list[float]]) -> list[baseline.NearbyReport]:
    """Community reports from the last 30 days within REPORT_RADIUS_M of the line."""
    if not coords:
        return []
    box = BBox.of_geometry({"type": "LineString", "coordinates": coords})
    now = datetime.now(UTC)
    rows = local_store.list_reports(
        box.min_lon - _ROUTE_BUFFER_DEG,
        box.min_lat - _ROUTE_BUFFER_DEG,
        box.max_lon + _ROUTE_BUFFER_DEG,
        box.max_lat + _ROUTE_BUFFER_DEG,
        limit=500,
        since=now - REPORT_LOOKBACK,
    )
    nearby = []
    for row in rows:
        if point_to_line_m(row["latitude"], row["longitude"], coords) > baseline.REPORT_RADIUS_M:
            continue
        occurred = datetime.fromisoformat(row["occurred_at"])
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=UTC)
        nearby.append(baseline.NearbyReport(
            id=row["id"],
            verified=row["confirmations"] >= settings.report_verification_threshold,
            age_hours=(now - occurred).total_seconds() / 3600,
        ))
    return nearby


def _explanation(passed, contributions: list[dict], *, estimated: bool) -> str:
    parts = []
    if estimated:
        parts.append("Route engine unavailable: estimated from straight-line distance.")
    if passed:
        areas = "; ".join(
            f"{z.name.title()}: {z.crime_rate_per_100k:g} violent crimes per 100,000/yr "
            f"({_ZONE_LABEL_TEXT[zones.label_for_score(z.safety_score)]})"
            for z in passed
        )
        parts.append(f"Passes through {areas}.")
    else:
        parts.append("No area crime data loaded for this route yet.")
    for c in contributions:
        if c["factor"] == "recent_reports":
            parts.append(c["detail"][0].upper() + c["detail"][1:] + ".")
        elif c["factor"] == "time_of_day" and c["impact"] < 0:
            parts.append(f"Lower at {c['detail']}.")
    parts.append(_NOT_YET_SCORED)
    return " ".join(parts)


def score_geometry(geometry: dict, *, hour: int | None = None, estimated: bool = False) -> tuple[float, str]:
    """(tryghedsscore, NF8 explanation) for one route geometry."""
    coords = geometry.get("coordinates", [])
    passed = zones.zones_along(coords)
    if hour is None:
        hour = datetime.now(LOCAL_TZ).hour
    score, contributions = baseline.score_route(
        [z.safety_score for z in passed], _reports_near(coords), hour, settings.dp_epsilon
    )
    return score, _explanation(passed, contributions, estimated=estimated)


def _option(duration_minutes: float, distance_meters: float, geometry: dict, *, estimated: bool = False) -> RouteOption:
    score, explanation = score_geometry(geometry, estimated=estimated)
    return RouteOption(
        duration_minutes=round(duration_minutes, 1),
        distance_meters=round(distance_meters),
        safety_score=score,
        safety_label=label_for_score(score),
        explanation=explanation,
        geometry=geometry,
    )


def _fallback_routes(origin: LatLon, destination: LatLon, mode: str) -> list[RouteOption]:
    """Estimated routes when OSRM is unreachable (NF7). Distance and time
    come from the straight-line distance (US-10), not fixed numbers."""
    straight = haversine_m(origin.lat, origin.lon, destination.lat, destination.lon)
    distance = straight * DETOUR_FACTOR
    minutes = distance / SPEED_M_PER_MIN[mode]
    direct = {
        "type": "LineString",
        "coordinates": [[origin.lon, origin.lat], [destination.lon, destination.lat]],
    }
    # A visibly different second line, bowed ~10 % of the trip to one side.
    d_lon, d_lat = destination.lon - origin.lon, destination.lat - origin.lat
    mid = [(origin.lon + destination.lon) / 2 - d_lat * 0.1, (origin.lat + destination.lat) / 2 + d_lon * 0.1]
    bowed = {"type": "LineString", "coordinates": [[origin.lon, origin.lat], mid, [destination.lon, destination.lat]]}
    return [
        _option(minutes, distance, direct, estimated=True),
        _option(minutes * 1.1, distance * 1.1, bowed, estimated=True),
    ]


async def find_routes(origin: LatLon, destination: LatLon, mode: str = "walking") -> list[RouteOption]:
    """Candidate routes, fastest first, each with a tryghedsscore.

    ``mode``: walking or cycling (US-37). Driving is out of scope (F15).
    """
    if mode not in osrm.MODES:
        raise UnsupportedModeError(mode)
    try:
        osrm_routes = await osrm.fetch_routes(origin.lat, origin.lon, destination.lat, destination.lon, mode)
    except osrm.OsrmUnavailableError:
        return _fallback_routes(origin, destination, mode)

    osrm_routes = sorted(osrm_routes, key=lambda r: r["duration"])
    return [_option(route["duration"] / 60, route["distance"], route["geometry"]) for route in osrm_routes]
