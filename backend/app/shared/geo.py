"""Value objects shared across resources."""
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
