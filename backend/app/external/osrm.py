"""OSRM (Open Source Routing Machine) adapter — afsnit 4.3.2 "Backend API - OSRM".

OSRM only knows geometry and walking time; SafeRoute adds the
tryghedsscore on top (api/routes/service.py). Self-hosted in the target
deployment (figur 4.3); OSRM_SERVER_URL points at the public demo instance
in development, so switching is a config change only.
"""
import httpx

from app.config import settings

# Short on purpose: a hanging OSRM must hand over to the NF7 fallback well
# within NF1's 10 s budget (ch. 6, I1.7 measured 10.7 s with a 10 s timeout).
# Async, so a slow OSRM never blocks other requests (NF1).
TIMEOUT_SECONDS = 3


class OsrmUnavailableError(Exception):
    """OSRM could not be reached or returned something unusable (NF7 fallback trigger)."""


async def fetch_walking_routes(from_lat: float, from_lon: float, to_lat: float, to_lon: float) -> list[dict]:
    """Up to three alternative foot routes as raw OSRM route objects
    (``duration`` s, ``distance`` m, GeoJSON ``geometry``).

    Raises OsrmUnavailableError on HTTP errors, timeouts, invalid JSON or an
    empty result — the caller decides how to degrade.
    """
    # OSRM expects lon,lat — the one place the coordinate order is swapped.
    url = f"{settings.osrm_server_url}/route/v1/foot/{from_lon},{from_lat};{to_lon},{to_lat}"
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
