"""Value objects shared across resources."""
import itertools
import math
from typing import NamedTuple


class BBox(NamedTuple):
    """Map viewport, as sent by the Mobile Client: ``minLon,minLat,maxLon,maxLat``."""

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    @classmethod
    def parse(cls, raw: str) -> "BBox":
        """Raises ValueError unless ``raw`` is four comma-separated numbers."""
        parts = [float(part) for part in raw.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must be minLon,minLat,maxLon,maxLat")
        return cls(*parts)

    @classmethod
    def of_geometry(cls, geometry: dict) -> "BBox":
        """Bounding box of any GeoJSON geometry ([lon, lat] positions, any nesting)."""
        lons, lats = [], []

        def walk(coords):
            if isinstance(coords[0], (int, float)):
                lons.append(coords[0])
                lats.append(coords[1])
            else:
                for c in coords:
                    walk(c)

        walk(geometry["coordinates"])
        return cls(min(lons), min(lats), max(lons), max(lats))

    def contains(self, lon: float, lat: float) -> bool:
        return self.min_lon <= lon <= self.max_lon and self.min_lat <= lat <= self.max_lat

    def intersects(self, other: "BBox") -> bool:
        return (
            self.min_lon <= other.max_lon
            and self.max_lon >= other.min_lon
            and self.min_lat <= other.max_lat
            and self.max_lat >= other.min_lat
        )

    def __str__(self) -> str:
        return ",".join(str(v) for v in self)


class LatLon(NamedTuple):
    """A point as sent by the Mobile Client: ``lat,lon`` (note: OSRM wants lon,lat)."""

    lat: float
    lon: float

    @classmethod
    def parse(cls, raw: str) -> "LatLon":
        parts = [float(part) for part in raw.split(",")]
        if len(parts) != 2:
            raise ValueError("point must be lat,lon")
        return cls(*parts)


# --- Distances (US-10, ML-03) ------------------------------------------------
# Equirectangular approximation: well under 1 % error at city scale, and far
# cheaper than a geodesic library for the hundreds of points a route has.
EARTH_RADIUS_M = 6_371_000


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def point_to_line_m(lat: float, lon: float, line: list[list[float]]) -> float:
    """Shortest distance in metres from a point to a GeoJSON LineString's
    coordinates ([lon, lat] pairs)."""
    if not line:
        return float("inf")
    if len(line) == 1:
        return haversine_m(lat, lon, line[0][1], line[0][0])
    k = math.cos(math.radians(lat))  # metres per degree of longitude shrink with latitude
    m_per_deg = math.pi * EARTH_RADIUS_M / 180
    px, py = lon * k * m_per_deg, lat * m_per_deg
    best = float("inf")
    for (lon1, lat1), (lon2, lat2) in itertools.pairwise(line):
        ax, ay = lon1 * k * m_per_deg, lat1 * m_per_deg
        bx, by = lon2 * k * m_per_deg, lat2 * m_per_deg
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
        cx, cy = ax + t * dx, ay + t * dy
        best = min(best, math.hypot(px - cx, py - cy))
    return best


def simplify_ring(ring: list[list[float]], tolerance: float) -> list[list[float]]:
    """Douglas-Peucker on one closed ring ([lon, lat] points), tolerance in
    degrees. Keeps at least 4 points so the ring stays a valid polygon."""
    if len(ring) <= 4:
        return ring

    def perpendicular(p, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if dx == 0 and dy == 0:
            return math.hypot(p[0] - a[0], p[1] - a[1])
        return abs(dy * p[0] - dx * p[1] + b[0] * a[1] - b[1] * a[0]) / math.hypot(dx, dy)

    keep = [False] * len(ring)
    keep[0] = keep[-1] = True
    stack = [(0, len(ring) - 1)]
    while stack:
        start, end = stack.pop()
        best, index = 0.0, -1
        for i in range(start + 1, end):
            d = perpendicular(ring[i], ring[start], ring[end])
            if d > best:
                best, index = d, i
        if index != -1 and best > tolerance:
            keep[index] = True
            stack.extend([(start, index), (index, end)])
    simplified = [pt for pt, k in zip(ring, keep) if k]
    if len(simplified) < 4:
        return ring
    return simplified


def simplify_geometry(geometry: dict, tolerance: float) -> dict:
    """Simplified copy of a GeoJSON Polygon/MultiPolygon (US-20: lighter map payload)."""
    if geometry["type"] == "Polygon":
        return {"type": "Polygon", "coordinates": [simplify_ring(r, tolerance) for r in geometry["coordinates"]]}
    if geometry["type"] == "MultiPolygon":
        return {
            "type": "MultiPolygon",
            "coordinates": [[simplify_ring(r, tolerance) for r in poly] for poly in geometry["coordinates"]],
        }
    return geometry
