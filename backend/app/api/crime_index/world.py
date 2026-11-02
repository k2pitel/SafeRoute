"""Country and city safety indices from free official data (F4 extension).

A Numbeo-style Crime Index / Safety Index without Numbeo's paid data:

    crime_index  = the country's percentile (0–100, higher = more crime) on
                   homicides per 100,000 (World Bank / UNODC)
    safety_index = 100 − crime_index

Homicides only, on purpose: it is the one crime measure recorded the same
way in every country. The Eurostat survey "% reporting crime, violence or
vandalism in their area" is returned alongside but kept out of the index:
it measures what people notice and complain about, which varies with
expectations (the Netherlands reports 16.7 %, Poland 2.8 %), and mixing a
36-country percentile with a 196-country one let the survey decide the
order inside Europe (it ranked Romania below Denmark despite ~30 % more
homicides). Cities use the Eurostat perception survey directly: the share
who agree they feel safe walking alone at night.
"""
import logging
from datetime import UTC, datetime

import httpx

from app.datalag import world_safety_cache
from app.datalag.world_safety_cache import WorldSafety
from app.external import eurostat, worldbank

logger = logging.getLogger("saferoute.world_safety")

# Eurostat uses EL for Greece and UK for the United Kingdom; ISO 3166 uses GR/GB.
_EUROSTAT_TO_ISO2 = {"EL": "GR", "UK": "GB"}

# Eurostat city codes start with the country (DK001C → DK).
_CITY_COUNTRY_TO_ISO2 = _EUROSTAT_TO_ISO2

SOURCES = {
    "homicides": "World Bank, VC.IHR.PSRC.P5 (UNODC), CC BY 4.0",
    "crime_in_area": "Eurostat, ilc_mddw03 (EU-SILC)",
    "night_safety": "Eurostat, urb_percep (Perception survey on quality of life in European cities)",
}


def _percentiles(values: dict[str, float]) -> dict[str, float]:
    """Share (0–100) of the other entries with a lower value."""
    if len(values) < 2:
        return {k: 50.0 for k in values}
    ordered = sorted(values.values())
    n = len(ordered) - 1
    return {k: round(sum(1 for x in ordered if x < v) / n * 100, 1) for k, v in values.items()}


def _clean_city_name(name: str) -> str:
    """'København (greater city)' → 'København'."""
    return name.split("(")[0].strip()


def build(homicides: dict[str, dict], crime_in_area: dict[str, dict], cities: dict[str, dict]) -> WorldSafety:
    countries: dict[str, dict] = {}
    for iso2, h in homicides.items():
        countries[iso2] = {
            "iso2": iso2,
            "name": h["name"],
            "region": h["region"],
            "homicides_per_100k": h["homicides_per_100k"],
            "homicides_year": h["year"],
            "crime_in_area_percent": None,
            "crime_in_area_year": None,
        }
    eu = crime_in_area.get("EU27_2020")
    for geo, c in crime_in_area.items():
        iso2 = _EUROSTAT_TO_ISO2.get(geo, geo)
        if iso2 in countries:
            countries[iso2]["crime_in_area_percent"] = c["percent"]
            countries[iso2]["crime_in_area_year"] = c["year"]

    homicide_pct = _percentiles({k: c["homicides_per_100k"] for k, c in countries.items()})
    for iso2, c in countries.items():
        c["crime_index"] = homicide_pct[iso2]
        c["safety_index"] = round(100 - c["crime_index"], 1)
        c["measures"] = ["homicides"]  # crime_in_area is shown, not scored (see module docstring)

    city_records: dict[str, dict] = {}
    for code, city in cities.items():
        night = city["city"]
        hood = city["neighbourhood"]
        country = _CITY_COUNTRY_TO_ISO2.get(code[:2], code[:2])
        record = {
            "code": code,
            "name": _clean_city_name(city["name"]),
            "country_iso2": country,
            "country": countries.get(country, {}).get("name", country),
            "year": city["year"],
            "night_safe_percent": round(night["strongly_agree"] + night["somewhat_agree"], 1),
            "night_unsafe_percent": round(night["somewhat_disagree"] + night["strongly_disagree"], 1),
            "night_strongly_agree_percent": night["strongly_agree"],
            "neighbourhood_night_safe_percent": (
                round(hood["strongly_agree"] + hood["somewhat_agree"], 1)
                if "strongly_agree" in hood and "somewhat_agree" in hood
                else None
            ),
        }
        city_records[code] = record
    ranked = sorted(city_records.values(), key=lambda r: r["night_safe_percent"], reverse=True)
    for rank, record in enumerate(ranked, start=1):
        record["rank"] = rank

    return WorldSafety(
        countries=countries,
        cities=city_records,
        eu_crime_in_area_percent=eu["percent"] if eu else None,
        eu_crime_in_area_year=eu["year"] if eu else None,
        fetched_at=datetime.now(UTC),
    )


async def refresh_cache() -> int:
    """Fetch all three sources and swap the cache. Keeps the previous data
    if any source fails (NF7). Returns the number of countries cached."""
    async with httpx.AsyncClient(timeout=eurostat.TIMEOUT_SECONDS) as client:
        try:
            homicides = await worldbank.fetch_homicide_rates(client)
            crime_in_area = await eurostat.fetch_crime_in_area(client)
            cities = await eurostat.fetch_city_night_safety(client)
        except (*eurostat.FETCH_ERRORS, *worldbank.FETCH_ERRORS) as exc:
            logger.warning("world_safety: fetch failed, keeping previous data (%s)", exc)
            return len(world_safety_cache.get().countries)
    if len(homicides) < 100 or len(cities) < 30:
        logger.warning("world_safety: implausibly little data (%d countries, %d cities); kept previous",
                       len(homicides), len(cities))
        return len(world_safety_cache.get().countries)
    world_safety_cache.replace(build(homicides, crime_in_area, cities))
    logger.info("world_safety: %d countries, %d cities", len(homicides), len(cities))
    return len(homicides)


# --- Read side (Backend API) ------------------------------------------------

def country_ranking() -> list[dict]:
    """All countries, most crime first (rank 1 = highest crime index)."""
    data = world_safety_cache.get()
    ranked = sorted(data.countries.values(), key=lambda c: c["crime_index"], reverse=True)
    return [{**c, "rank": i} for i, c in enumerate(ranked, start=1)]


def city_ranking() -> list[dict]:
    """European cities, safest at night first."""
    return sorted(world_safety_cache.get().cities.values(), key=lambda r: r["rank"])


def country(iso2: str) -> dict | None:
    for c in country_ranking():
        if c["iso2"] == iso2:
            return c
    return None


def find_city(name: str, country_iso2: str | None = None) -> dict | None:
    """Survey city by name, e.g. 'København', 'Copenhagen' or 'Aalborg'."""
    aliases = {"copenhagen": "københavn", "munich": "münchen", "cologne": "köln", "vienna": "wien",
               "prague": "praha", "warsaw": "warszawa", "rome": "roma", "lisbon": "lisboa"}
    key = name.strip().lower()
    key = aliases.get(key, key)
    for record in world_safety_cache.get().cities.values():
        if country_iso2 and record["country_iso2"] != country_iso2:
            continue
        if record["name"].lower() == key:
            return record
    return None


def eu_average() -> dict:
    data = world_safety_cache.get()
    return {"crime_in_area_percent": data.eu_crime_in_area_percent, "year": data.eu_crime_in_area_year}


def loaded() -> bool:
    return bool(world_safety_cache.get().countries)


def fetched_at() -> datetime | None:
    return world_safety_cache.get().fetched_at
