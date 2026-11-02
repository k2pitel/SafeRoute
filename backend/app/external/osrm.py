"""OSRM (Open Source Routing Machine) adapter — afsnit 4.3.2 "Backend API - OSRM".

OSRM only knows geometry and travel time; SafeRoute adds the
tryghedsscore on top (api/routes/service.py). Self-hosted in the target
deployment (figur 4.3); OSRM_SERVER_URL points at the public demo instance
in development, so switching is a config change only.

US-37: walking and cycling. The public FOSSGIS instance serves one profile
per path (routed-foot, routed-bike); a self-hosted OSRM serves profiles by
name on one server (/route/v1/foot, /route/v1/bike).
"""
import httpx

from app.config import settings

# Short on purpose: a hanging OSRM must hand over to the NF7 fallback well
# within NF1's 10 s budget (ch. 6, I1.7 measured 10.7 s with a 10 s timeout).
# Async, so a slow OSRM never blocks other requests (NF1).
TIMEOUT_SECONDS = 3

MODES = ("walking", "cycling")
_PROFILE = {"walking": "foot", "cycling": "bike"}


class OsrmUnavailableError(Exception):
    """OSRM could not be reached or returned something unusable (NF7 fallback trigger)."""


def server_for(mode: str) -> str:
    """Base URL for a mode. A public routed-foot URL is swapped to routed-bike
    for cycling; any other URL is assumed to serve every profile."""
    base = settings.osrm_server_url.rstrip("/")
    if mode == "cycling" and base.endswith("/routed-foot"):
        return base.removesuffix("/routed-foot") + "/routed-bike"
    return base


async def fetch_routes(
    from_lat: float, from_lon: float, to_lat: float, to_lon: float, mode: str = "walking"
) -> list[dict]:
    """Up to three alternative routes as raw OSRM route objects
    (``duration`` s, ``distance`` m, GeoJSON ``geometry``).

    Raises OsrmUnavailableError on HTTP errors, timeouts, invalid JSON or an
    empty result — the caller decides how to degrade.
    """
    # OSRM expects lon,lat — the one place the coordinate order is swapped.
    url = f"{server_for(mode)}/route/v1/{_PROFILE[mode]}/{from_lon},{from_lat};{to_lon},{to_lat}"
    params = {"overview": "full", "geometries": "geojson", "alternatives": "true"}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OsrmUnavailableError(str(exc)) from exc

    routes = data.get("routes") or []
    if not routes:
        raise OsrmUnavailableError("OSRM returned no routes")
    return routes


async def fetch_walking_routes(from_lat: float, from_lon: float, to_lat: float, to_lon: float) -> list[dict]:
    """Kept for existing callers; same as ``fetch_routes(..., "walking")``."""
    return await fetch_routes(from_lat, from_lon, to_lat, to_lon, "walking")
