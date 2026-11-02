"""GET /api/crime-index (F4)."""
from datetime import datetime

from pydantic import BaseModel


class CrimeIndexOut(BaseModel):
    """City safety overview built from real data (US-29): the municipality's
    official violent-crime rate, how it compares nationally, and recent
    community reports and news. No survey numbers: there is no free source."""

    city: str  # what the user asked for, e.g. "Aarhus"
    municipality: str  # the municipality the numbers are for
    crime_index: float  # 0–100: share of municipalities with a lower rate
    safety_index: float  # 0–100: the zone tryghedsscore × 10
    safety_label: str  # 'unsafe' | 'mixed' | 'safe' (same as the map)
    violent_crimes_per_year: float
    population: int
    rate_per_100k: float
    national_rate_per_100k: float
    rank: int  # 1 = highest rate in the country
    municipalities_ranked: int
    recent_reports_30d: int
    recent_news_90d: int
    summary: str
    data_period: str | None  # e.g. "2025K3-2026K2", or the chosen range "2024–2025"
    from_year: int | None = None  # set when a period filter was used
    to_year: int | None = None
    last_updated: datetime | None  # when the statistics were fetched
    # Free stand-ins for paid crime-index data (Eurostat, World Bank):
    perception: "CitySafetyOut | None" = None  # survey: feeling safe at night, if the city was surveyed
    country: "CountryContext | None" = None


class CountrySafetyOut(BaseModel):
    """One row of the country ranking (free, official data; see api/crime_index/world.py)."""

    rank: int  # 1 = highest crime index
    iso2: str
    name: str
    region: str
    crime_index: float  # 0-100, percentile on homicides per 100,000
    safety_index: float  # 100 - crime_index
    homicides_per_100k: float
    homicides_year: str
    crime_in_area_percent: float | None  # % reporting crime/violence/vandalism nearby (Eurostat); shown, not scored
    crime_in_area_year: str | None
    measures: list[str]


class CitySafetyOut(BaseModel):
    """One European city from the Eurostat perception survey."""

    rank: int  # 1 = most residents feel safe at night
    code: str
    name: str
    country_iso2: str
    country: str
    year: str
    night_safe_percent: float  # agree they feel safe walking alone at night in the city
    night_unsafe_percent: float
    night_strongly_agree_percent: float
    neighbourhood_night_safe_percent: float | None


class CountryContext(BaseModel):
    """How the city's country compares (Crime Index screen)."""

    name: str
    rank: int
    countries_ranked: int
    crime_index: float
    safety_index: float
    homicides_per_100k: float
    homicides_year: str
    crime_in_area_percent: float | None
    crime_in_area_year: str | None
    eu_crime_in_area_percent: float | None


class WorldSafetySources(BaseModel):
    homicides: str
    crime_in_area: str
    night_safety: str



class YearRange(BaseModel):
    min_year: int
    max_year: int


class AvailablePeriods(BaseModel):
    denmark: YearRange
    countries: YearRange | None


CrimeIndexOut.model_rebuild()
