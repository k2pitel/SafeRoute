"""In-memory cache of country and European-city safety data.

Like zone_cache: rebuilt by the Async Worker from public sources (Eurostat,
World Bank; worker/jobs.refresh_world_safety), read by the Backend API, so
a request never waits on an external API (NF7). The sources publish
yearly, so a daily refresh is plenty.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorldSafety:
    countries: dict[str, dict] = field(default_factory=dict)  # ISO2 → merged country record
    cities: dict[str, dict] = field(default_factory=dict)  # Eurostat city code → perception record
    eu_crime_in_area_percent: float | None = None
    eu_crime_in_area_year: str | None = None
    fetched_at: datetime | None = None


_data = WorldSafety()


def replace(data: WorldSafety) -> None:
    global _data
    _data = data


def get() -> WorldSafety:
    return _data
