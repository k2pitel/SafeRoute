"""Real Danish municipal crime data — Statistics Denmark (dst.dk) + open
municipality boundaries — used to color map zones by actual violent-crime
rate instead of mock data.

This is area-level (one score per municipality), not point-level: official
crime stats don't carry exact incident coordinates, only per-area counts.
That's exactly what a *zone* (polygon) needs, as opposed to an *incident*
pin (which would need a real point and isn't something this dataset can
give you) — see README > Database Schema for the same distinction between
`segment_scores`/zones and `incidents`.

Everything here is cached in memory and refreshed periodically (see
main.py's lifespan) rather than re-fetched per request, since the
underlying stats only change quarterly.
"""
import csv
import io
import logging
import statistics
from dataclasses import dataclass

import httpx

logger = logging.getLogger("saferoute.crime_stats")

STATBANK_TABLEINFO_URL = "https://api.statbank.dk/v1/tableinfo/{table}"
STATBANK_DATA_URL = "https://api.statbank.dk/v1/data"
MUNICIPALITY_BOUNDARIES_URL = "https://raw.githubusercontent.com/Neogeografen/dagi/master/geojson/kommuner.geojson"

VIOLENT_CRIME_CODE = "12"  # STRAF11 "Voldsforbrydelser i alt" (violent crimes, total)
QUARTERS_TO_SUM = 4  # trailing year, so small municipalities aren't just quarterly noise


@dataclass
class MunicipalityStats:
    name: str
    violent_crimes_per_year: float
    population: int
    crime_rate_per_100k: float
    safety_score: float  # 1-10, higher = safer
    geometry: dict  # GeoJSON Polygon/MultiPolygon


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace("-", " ")


async def _latest_quarters(client: httpx.AsyncClient, table: str, n: int) -> list[str]:
    resp = await client.get(STATBANK_TABLEINFO_URL.format(table=table))
    resp.raise_for_status()
    time_var = next(v for v in resp.json()["variables"] if v["id"] == "Tid")
    return [v["id"] for v in time_var["values"][-n:]]


async def _fetch_csv(client: httpx.AsyncClient, table: str, variables: list[dict]) -> list[dict]:
    resp = await client.post(STATBANK_DATA_URL, json={"table": table, "format": "CSV", "variables": variables})
    resp.raise_for_status()
    text = resp.content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text), delimiter=";"))


async def _fetch_violent_crime_by_area(client: httpx.AsyncClient) -> dict[str, float]:
    quarters = await _latest_quarters(client, "STRAF11", QUARTERS_TO_SUM)
    rows = await _fetch_csv(
        client,
        "STRAF11",
        [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "OVERTRÆD", "values": [VIOLENT_CRIME_CODE]},
            {"code": "Tid", "values": quarters},
        ],
    )
    totals: dict[str, float] = {}
    for row in rows:
        name = _normalize_name(row["OMRÅDE"])
        try:
            value = float(row["INDHOLD"])
        except ValueError:
            continue
        totals[name] = totals.get(name, 0) + value
    return totals


async def _fetch_population_by_area(client: httpx.AsyncClient) -> dict[str, int]:
    quarters = await _latest_quarters(client, "FOLK1A", 1)
    rows = await _fetch_csv(
        client,
        "FOLK1A",
        [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "KØN", "values": ["TOT"]},
            {"code": "ALDER", "values": ["IALT"]},
            {"code": "CIVILSTAND", "values": ["TOT"]},
            {"code": "Tid", "values": quarters},
        ],
    )
    populations: dict[str, int] = {}
    for row in rows:
        name = _normalize_name(row["OMRÅDE"])
        try:
            populations[name] = int(float(row["INDHOLD"]))
        except ValueError:
            continue
    return populations


async def _fetch_boundaries(client: httpx.AsyncClient) -> dict[str, dict]:
    resp = await client.get(MUNICIPALITY_BOUNDARIES_URL)
    resp.raise_for_status()
    geojson = resp.json()

    boundaries: dict[str, dict] = {}
    for feature in geojson["features"]:
        name = _normalize_name(feature["properties"]["KOMNAVN"])
        boundaries.setdefault(name, []).append(feature["geometry"])
    return boundaries


def _score_from_rates(rates: dict[str, float]) -> dict[str, float]:
    """
    Standard-deviations-from-the-national-average, not percentile rank.
    Percentile rank always colors a fixed third of the map "unsafe"
    regardless of how tight the real spread is — misleading for a
    genuinely near-normal, moderate-spread distribution like this one
    (mean/median both ~440 per 100k, stdev ~150). Z-score instead flags
    only actual statistical outliers, and a municipality sitting right at
    the national average lands near the "mixed" midpoint rather than being
    arbitrarily bucketed into a third.
    """
    if len(rates) < 2:
        return {name: 5.5 for name in rates}

    values = list(rates.values())
    mean = statistics.mean(values)
    stdev = statistics.stdev(values) or 1.0

    scores = {}
    for name, rate in rates.items():
        z = (rate - mean) / stdev
        scores[name] = round(min(10.0, max(1.0, 5.5 - z * 1.5)), 1)
    return scores


async def fetch_municipality_stats() -> list[MunicipalityStats]:
    async with httpx.AsyncClient(timeout=30) as client:
        crime_by_area, population_by_area, boundaries = None, None, None
        try:
            crime_by_area = await _fetch_violent_crime_by_area(client)
            population_by_area = await _fetch_population_by_area(client)
            boundaries = await _fetch_boundaries(client)
        except (httpx.HTTPError, KeyError, StopIteration) as exc:
            logger.warning("crime_stats: fetch failed, returning empty (%s)", exc)
            return []

    rates: dict[str, float] = {}
    for name, crimes in crime_by_area.items():
        population = population_by_area.get(name)
        if not population or name not in boundaries:
            continue  # regional/national aggregate rows (e.g. "Hele landet") won't match a boundary
        rates[name] = (crimes / population) * 100_000

    scores = _score_from_rates(rates)

    results = []
    for name, rate in rates.items():
        for geometry in boundaries[name]:
            results.append(
                MunicipalityStats(
                    name=name,
                    violent_crimes_per_year=crime_by_area[name],
                    population=population_by_area[name],
                    crime_rate_per_100k=round(rate, 1),
                    safety_score=scores[name],
                    geometry=geometry,
                )
            )
    return results


# --- In-memory cache -------------------------------------------------
# Refreshed periodically by main.py's lifespan, not per-request — the
# underlying stats only change quarterly, and the boundaries file is 2MB+.
_cache: list[MunicipalityStats] = []


async def refresh_cache() -> None:
    global _cache
    stats = await fetch_municipality_stats()
    if stats:
        _cache = stats
        logger.info("crime_stats: cached %d municipality polygons", len(stats))


def get_cached_stats() -> list[MunicipalityStats]:
    return _cache
