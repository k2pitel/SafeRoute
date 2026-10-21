"""Small builders for test data shared by unit and integration tests."""
from app.datalag.zone_cache import MunicipalityStats


def square(min_lon, min_lat, size=0.1):
    """GeoJSON Polygon: a size x size degree square."""
    ring = [
        [min_lon, min_lat],
        [min_lon + size, min_lat],
        [min_lon + size, min_lat + size],
        [min_lon, min_lat + size],
        [min_lon, min_lat],
    ]
    return {"type": "Polygon", "coordinates": [ring]}


def municipality(name, score, geometry):
    return MunicipalityStats(
        name=name, violent_crimes_per_year=0, population=1, crime_rate_per_100k=0, safety_score=score, geometry=geometry
    )
