"""Danish municipality crime statistics for a chosen year range.

The zone cache always holds the latest four quarters (what the map shows).
The Crime Index screen can also ask for e.g. 2024–2025: this fetches those
quarters from Danmarks Statistik on demand, turns them into a yearly rate
per 100,000 (so a 2-year range is comparable with a 1-year one) and caches
the result, since the numbers for a past period never change.

Population is taken from the last quarter of the period (FOLK1A starts in
2008, which is why that is the earliest year offered).
"""
import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from app.api.zones import service as zones
from app.api.zones.crime_stats import score_from_rates
from app.external import statistics_denmark as dst

MIN_YEAR = 2008
CACHE_SECONDS = 6 * 60 * 60  # the newest quarter can appear; older periods never change
_MAX_CACHED_PERIODS = 30


class InvalidPeriodError(ValueError):
    pass


class SourceUnavailableError(Exception):
    pass


class DataNotLoadedError(Exception):
    """Municipality list not loaded yet (the zone cache fills it on startup)."""


@dataclass
class PeriodStats:
    from_year: int
    to_year: int
    quarters: list[str]
    municipalities: dict[str, dict]  # name → {violent_crimes_per_year, population, rate_per_100k, safety_score}
    national_rate_per_100k: float

    @property
    def label(self) -> str:
        """'2024–2025', or the exact quarters when the last year isn't complete."""
        if self.quarters[-1].endswith("K4") and self.quarters[0].endswith("K1"):
            return str(self.from_year) if self.from_year == self.to_year else f"{self.from_year}–{self.to_year}"
        return f"{self.quarters[0]}–{self.quarters[-1]}"

    @property
    def start(self) -> datetime:
        return datetime(self.from_year, 1, 1, tzinfo=UTC)

    @property
    def end(self) -> datetime:
        return datetime(self.to_year + 1, 1, 1, tzinfo=UTC)


_cache: dict[tuple[int, int], tuple[float, PeriodStats]] = {}
_lock = asyncio.Lock()


def validate(from_year: int, to_year: int) -> None:
    this_year = datetime.now(UTC).year
    if from_year > to_year:
        raise InvalidPeriodError("'from' must be before or equal to 'to'")
    if from_year < MIN_YEAR or to_year > this_year:
        raise InvalidPeriodError(f"Years must be between {MIN_YEAR} and {this_year}")


async def stats_for(from_year: int, to_year: int) -> PeriodStats:
    validate(from_year, to_year)
    key = (from_year, to_year)
    async with _lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < CACHE_SECONDS:
            return hit[1]

        known = {m.name for m in zones.all_municipalities()}
        if not known:
            raise DataNotLoadedError()

        try:
            async with httpx.AsyncClient(timeout=dst.TIMEOUT_SECONDS) as client:
                quarters = [
                    q for q in await dst.available_quarters(client, "STRAF11") if from_year <= int(q[:4]) <= to_year
                ]
                if not quarters:
                    raise InvalidPeriodError(f"No crime statistics for {from_year}–{to_year} yet")
                population_quarters = await dst.available_quarters(client, "FOLK1A")
                population_quarter = max(q for q in population_quarters if q <= quarters[-1])
                crimes = await dst.fetch_violent_crime_for_quarters(client, quarters)
                population = await dst.fetch_population_for_quarter(client, population_quarter)
        except dst.FETCH_ERRORS as exc:
            raise SourceUnavailableError(str(exc)) from exc

        years = len(quarters) / 4
        per_year = {n: crimes[n] / years for n in known if n in crimes and population.get(n)}
        rates = {n: per_year[n] / population[n] * 100_000 for n in per_year}
        scores = score_from_rates(rates)
        total_population = sum(population[n] for n in per_year)
        stats = PeriodStats(
            from_year=from_year,
            to_year=to_year,
            quarters=quarters,
            municipalities={
                n: {
                    "violent_crimes_per_year": round(per_year[n], 1),
                    "population": population[n],
                    "rate_per_100k": round(rates[n], 1),
                    "safety_score": scores[n],
                }
                for n in rates
            },
            national_rate_per_100k=round(sum(per_year.values()) / total_population * 100_000, 1),
        )
        if len(_cache) >= _MAX_CACHED_PERIODS:
            _cache.pop(min(_cache, key=lambda k: _cache[k][0]))
        _cache[key] = (time.time(), stats)
        return stats
