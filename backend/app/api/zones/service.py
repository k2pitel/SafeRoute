"""Zones for the colour-coded map (F7) and client-side geofencing (F5).

Reads the zone cache the Async Worker keeps fresh (api/zones/crime_stats.py)
and filters it to the requested viewport with a bounding-box overlap test.
"""
from app.api.zones.schemas import ZoneOut
from app.datalag import zone_cache
from app.datalag.zone_cache import MunicipalityStats
from app.shared.geo import BBox


def label_for_score(score: float) -> str:
    # "No color" is the default — only areas with an actual signal should be
    # flagged. score is 5.5 - 1.5*z (see crime_stats.score_from_rates), so
    # these cutoffs correspond to roughly +1.25 / +0.75 standard deviations
    # above the national average violent-crime rate — genuine statistical
    # standouts, maybe the top ~10-15% of municipalities, not a third of the map.
    if score < 3.6:
        return "unsafe"
    if score < 4.4:
        return "mixed"
    return "safe"


def zones_in_bbox(bbox: BBox) -> list[ZoneOut]:
    """Empty if the cache hasn't loaded yet or the source was unreachable —
    never placeholder shapes."""
    # Municipalities with disconnected land (islands, exclaves) come back as
    # multiple polygon features sharing one name — count occurrences so each
    # piece still gets a unique id (a bare name would collide and break
    # React's list keys on the mobile side).
    seen_counts: dict[str, int] = {}
    zones = []
    for entry in zone_cache.get_all():
        if not entry.bbox.intersects(bbox):
            continue
        seen_counts[entry.name] = seen_counts.get(entry.name, 0) + 1
        piece_id = entry.name if seen_counts[entry.name] == 1 else f"{entry.name}-{seen_counts[entry.name]}"
        zones.append(
            ZoneOut(
                id=piece_id,
                safety_score=entry.safety_score,
                safety_label=label_for_score(entry.safety_score),
                geometry=entry.geometry,
            )
        )
    return zones


def cached_zone_count() -> int:
    return len(zone_cache.get_all())


def _outer_rings(geometry: dict) -> list[list[list[float]]]:
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"][0]]
    if geometry["type"] == "MultiPolygon":
        return [polygon[0] for polygon in geometry["coordinates"]]
    return []


def _inside_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    """Ray casting, same algorithm as the Mobile Client's geofence."""
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def zones_along(coordinates: list[list[float]], max_samples: int = 25) -> list[MunicipalityStats]:
    """Municipalities a GeoJSON line ([lon, lat] points) passes through, in
    route order, each once. Samples at most ``max_samples`` points to keep
    route requests fast (NF1)."""
    if not coordinates:
        return []
    step = max(1, len(coordinates) // max_samples)
    points = coordinates[::step] + [coordinates[-1]]

    found: dict[str, MunicipalityStats] = {}
    for lon, lat in points:
        for entry in zone_cache.get_all():
            if entry.name in found:
                continue
            if not entry.bbox.contains(lon, lat):
                continue
            if any(_inside_ring(lon, lat, ring) for ring in _outer_rings(entry.geometry)):
                found[entry.name] = entry
    return list(found.values())
