"""In-memory cache of municipality zones (polygon + tryghedsscore).

Kept in memory rather than persisted: it can always be rebuilt from the
public source, and the underlying statistics only change quarterly. The
Async Worker rebuilds it periodically (worker/jobs.py); GET /api/zones only
ever reads it, so a request never waits on Danmarks Statistik (NF7).
"""
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property

from app.shared.geo import BBox, simplify_geometry

# About 50 m. Enough detail for a city-level map; cuts Denmark's ~41,000
# vertices to a fraction (US-20). Point-in-polygon tests keep using the
# full geometry.
DISPLAY_TOLERANCE_DEG = 0.0005


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

    @cached_property
    def display_geometry(self) -> dict:
        """Simplified outline for drawing on the map."""
        return simplify_geometry(self.geometry, DISPLAY_TOLERANCE_DEG)


@dataclass
class DataInfo:
    """Where the cached numbers come from (DP-07): shown as "Data from ..."."""

    crime_period: str  # e.g. "2025K3-2026K2"
    population_period: str  # e.g. "2026K3"
    fetched_at: datetime


_zones: list[MunicipalityStats] = []
_info: DataInfo | None = None


def set_info(info: DataInfo) -> None:
    global _info
    _info = info


def get_info() -> DataInfo | None:
    return _info


def replace_all(zones: list[MunicipalityStats]) -> None:
    """Swap in a freshly computed set. The swap is a single assignment, so a
    concurrent reader sees either the old or the new set, never a mix."""
    global _zones
    _zones = list(zones)


def get_all() -> list[MunicipalityStats]:
    return _zones


def clear() -> None:
    replace_all([])
