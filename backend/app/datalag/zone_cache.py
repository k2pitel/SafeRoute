"""In-memory cache of municipality zones (polygon + tryghedsscore).

Kept in memory rather than persisted: it can always be rebuilt from the
public source, and the underlying statistics only change quarterly. The
Async Worker rebuilds it periodically (worker/jobs.py); GET /api/zones only
ever reads it, so a request never waits on Danmarks Statistik (NF7).
"""
from dataclasses import dataclass
from functools import cached_property

from app.shared.geo import BBox


@dataclass
class MunicipalityStats:
    name: str
    violent_crimes_per_year: float
    population: int
    crime_rate_per_100k: float
    safety_score: float  # 1-10, higher = safer
    geometry: dict  # GeoJSON Polygon/MultiPolygon

    @cached_property
    def bbox(self) -> BBox:
        """Computed once per entry — polygons have thousands of vertices."""
        return BBox.of_geometry(self.geometry)


_zones: list[MunicipalityStats] = []


def replace_all(zones: list[MunicipalityStats]) -> None:
    """Swap in a freshly computed set. The swap is a single assignment, so a
    concurrent reader sees either the old or the new set, never a mix."""
    global _zones
    _zones = list(zones)


def get_all() -> list[MunicipalityStats]:
    return _zones


def clear() -> None:
    replace_all([])
