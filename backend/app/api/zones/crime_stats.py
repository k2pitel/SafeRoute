"""Municipal crime statistics -> zone tryghedsscore (F7, F5).

The only place real crime data already drives a score. Official Danish
data has no per-incident coordinates, only counts per municipality, so a
zone is a municipality polygon. The score is computed in three steps:

1. violent crimes (STRAF11, code 12) summed over the latest four quarters,
2. rate per 100,000 inhabitants (FOLK1A),
3. z-score against the national average:
   ``score = clamp(5.5 - 1.5 * z, 1, 10)``.

Fetching lives in external/statistics_denmark.py, storage in
datalag/zone_cache.py; this module is the domain logic in between. The
Async Worker calls ``refresh_cache`` periodically (worker/jobs.py).
"""
import logging
import statistics
from datetime import UTC, datetime

import httpx

from app.datalag import zone_cache
from app.datalag.zone_cache import DataInfo, MunicipalityStats
from app.external import statistics_denmark

logger = logging.getLogger("saferoute.crime_stats")


def score_from_rates(rates: dict[str, float]) -> dict[str, float]:
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


def build_municipality_stats(
    crime_by_area: dict[str, float],
    population_by_area: dict[str, int],
    boundaries: dict[str, list[dict]],
) -> list[MunicipalityStats]:
    """Join the three sources and score every municipality, one entry per polygon piece."""
    rates: dict[str, float] = {}
    for name, crimes in crime_by_area.items():
        population = population_by_area.get(name)
        if not population or name not in boundaries:
            continue  # regional/national aggregate rows (e.g. "Hele landet") won't match a boundary
        rates[name] = (crimes / population) * 100_000

    scores = score_from_rates(rates)

    return [
        MunicipalityStats(
            name=name,
            violent_crimes_per_year=crime_by_area[name],
            population=population_by_area[name],
            crime_rate_per_100k=round(rate, 1),
            safety_score=scores[name],
            geometry=geometry,
        )
        for name, rate in rates.items()
        for geometry in boundaries[name]
    ]


# DP-04 sanity check: Denmark has 98 municipalities (+ Christiansø). A
# snapshot with far fewer means a source changed shape; keep the old data.
MIN_MUNICIPALITIES = 95


class ValidationError(Exception):
    """A fetched snapshot failed the sanity checks (DP-04)."""


async def fetch_municipality_stats() -> tuple[list[MunicipalityStats], DataInfo | None]:
    """Fresh stats from the public sources; ([], None) if any source fails."""
    async with httpx.AsyncClient(timeout=statistics_denmark.TIMEOUT_SECONDS) as client:
        try:
            crime_by_area, quarters = await statistics_denmark.fetch_violent_crime_by_area(client)
            population_by_area, population_quarter = await statistics_denmark.fetch_population_by_area(client)
            boundaries = await statistics_denmark.fetch_municipality_boundaries(client)
        except statistics_denmark.FETCH_ERRORS as exc:
            logger.warning("crime_stats: fetch failed, returning empty (%s)", exc)
            return [], None
    info = DataInfo(
        crime_period=f"{quarters[0]}-{quarters[-1]}" if quarters else "unknown",
        population_period=population_quarter,
        fetched_at=datetime.now(UTC),
    )
    return build_municipality_stats(crime_by_area, population_by_area, boundaries), info


async def refresh_cache() -> int:
    """Rebuild the zone cache. Keeps the previous cache if the source is down
    or the new data fails validation (NF7). Returns how many polygons are
    now cached."""
    stats, info = await fetch_municipality_stats()
    if stats:
        municipalities = {s.name for s in stats}
        if len(municipalities) < MIN_MUNICIPALITIES:
            raise ValidationError(
                f"only {len(municipalities)} municipalities matched (expected at least "
                f"{MIN_MUNICIPALITIES}); kept the previous data"
            )
        zone_cache.replace_all(stats)
        if info:
            zone_cache.set_info(info)
        logger.info("crime_stats: cached %d municipality polygons (%s)", len(stats), info and info.crime_period)
    return len(zone_cache.get_all())
