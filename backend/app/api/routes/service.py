"""Rutetjenesten — Backend API's part of UC1 (F1, NF1, NF7).

Gets route geometries from OSRM (external/osrm.py) and attaches a
tryghedsscore to each. If OSRM fails in any way, ``_fallback_routes``
answers instead, so the user always gets a reply (NF7).

The score is still a stand-in. The planned solution (afsnit 4.2.1) is to
look up precomputed scores in ``segment_scores`` for the segments the
route passes; that table isn't populated yet, so options are ranked
fastest-first and the fastest is rated least safe and the next the safest,
keeping the fast-vs-safe trade-off and the full RouteOption contract so
the Mobile Client won't change when real scoring is plugged in here.

NF8: every option carries an explanation. It only states what the system
actually knows — the municipalities the route passes through and their
official violent-crime rate (api/zones/service.py) — and says plainly that
street-level factors aren't scored yet, rather than inventing reasons.
"""
from app.api.routes.schemas import RouteOption
from app.api.zones import service as zones
from app.external import osrm
from app.shared.geo import LatLon

# Stand-in scores, see module docstring.
_FASTEST_SCORE = 4.2
_SAFEST_SCORE = 8.6
_OTHER_SCORE = 6.5


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
_NOT_YET_SCORED = "Street-level factors (lighting, recent reports) are not scored yet."


def explain(geometry: dict, *, estimated: bool = False) -> str:
    """NF8 explanation for one route, built from the zone data it passes through."""
    parts = []
    if estimated:
        parts.append("Route engine unavailable: straight-line estimate.")
    passed = zones.zones_along(geometry.get("coordinates", []))
    if passed:
        areas = "; ".join(
            f"{z.name.title()}: {z.crime_rate_per_100k:g} violent crimes per 100,000/yr "
            f"({_ZONE_LABEL_TEXT[zones.label_for_score(z.safety_score)]})"
            for z in passed
        )
        parts.append(f"Passes through {areas}.")
    else:
        parts.append("No area crime data loaded for this route yet.")
    parts.append(_NOT_YET_SCORED)
    return " ".join(parts)


def _option(
    duration_minutes: float, distance_meters: float, score: float, geometry: dict, *, estimated: bool = False
) -> RouteOption:
    return RouteOption(
        duration_minutes=duration_minutes,
        distance_meters=distance_meters,
        safety_score=score,
        safety_label=label_for_score(score),
        explanation=explain(geometry, estimated=estimated),
        geometry=geometry,
    )


def _fallback_routes(origin: LatLon, destination: LatLon) -> list[RouteOption]:
    """Straight-line stand-ins, used when OSRM is unreachable (NF7)."""
    fast = _option(30, 2400, _FASTEST_SCORE, estimated=True, geometry={
        "type": "LineString",
        "coordinates": [[origin.lon, origin.lat], [destination.lon, destination.lat]],
    })
    safe = _option(34, 2650, _SAFEST_SCORE, estimated=True, geometry={
        "type": "LineString",
        "coordinates": [
            [origin.lon, origin.lat],
            [(origin.lon + destination.lon) / 2, (origin.lat + destination.lat) / 2 + 0.001],
            [destination.lon, destination.lat],
        ],
    })
    return [safe, fast]


def _stand_in_scores(count: int) -> list[float]:
    if count == 1:
        return [_FASTEST_SCORE]
    return [_FASTEST_SCORE, _SAFEST_SCORE, *([_OTHER_SCORE] * (count - 2))]


async def find_routes(origin: LatLon, destination: LatLon, mode: str = "walking") -> list[RouteOption]:
    """Candidate routes, fastest first, each with a tryghedsscore.

    ``mode`` is accepted for the F10 contract but only walking is routed in
    this iteration (F15: no car navigation).
    """
    try:
        osrm_routes = await osrm.fetch_walking_routes(origin.lat, origin.lon, destination.lat, destination.lon)
    except osrm.OsrmUnavailableError:
        return _fallback_routes(origin, destination)

    osrm_routes = sorted(osrm_routes, key=lambda r: r["duration"])
    return [
        _option(route["duration"] / 60, route["distance"], score, route["geometry"])
        for route, score in zip(osrm_routes, _stand_in_scores(len(osrm_routes)))
    ]
