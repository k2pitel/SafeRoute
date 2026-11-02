"""Bytryghedsoversigt (F4) from real data (US-29).

Everything comes from sources the system already has: the municipality's
violent-crime rate (Danmarks Statistik, via the zone cache), its rank
nationally, community reports in it from the last 30 days and placed crime
news from the last 90 days. The summary is generated from those numbers —
no invented survey figures or contributor counts.
"""
from datetime import UTC, datetime, timedelta

from app.api.crime_index import periods, world
from app.api.news.places import coords_for, matches_city
from app.api.zones import service as zones
from app.datalag import local_store, news_archive, zone_cache


class CityNotFoundError(Exception):
    pass


class DataNotLoadedError(Exception):
    pass


def _clean(city: str) -> str:
    """'Aarhus, Denmark' → 'Aarhus'."""
    return city.split(",")[0].strip()


def _resolve(city: str):
    name = _clean(city)
    entry = zones.municipality_named(name)
    if entry:
        return entry
    point = coords_for(name)
    if point:
        return zones.municipality_at(*point)
    return None


def _reports_in(entry, since: datetime, until: datetime | None = None) -> int:
    box = entry.bbox
    rows = local_store.list_reports(box.min_lon, box.min_lat, box.max_lon, box.max_lat, limit=5000, since=since)
    count = 0
    for r in rows:
        if until is not None and datetime.fromisoformat(r["occurred_at"]).replace(tzinfo=UTC) >= until:
            continue
        if zones.municipality_at(r["latitude"], r["longitude"]) is entry:
            count += 1
    return count


def _news_in(name: str, since: datetime, until: datetime | None = None) -> int:
    count = 0
    for item in news_archive.load_items(limit=20000):
        published = item.published_at if item.published_at.tzinfo else item.published_at.replace(tzinfo=UTC)
        if published < since:
            break  # newest first
        if until is not None and published >= until:
            continue
        if matches_city(name, item.title, item.latitude, item.longitude):
            count += 1
    return count


def _summary(muni: str, rate: float, national: float, rank: int, total: int, label: str,
             reports: int, news: int, period: str | None, custom_period: bool = False) -> str:
    ratio = rate / national if national else 1.0
    if ratio >= 1.15:
        compare = f"{(ratio - 1) * 100:.0f}% above the national average"
    elif ratio <= 0.85:
        compare = f"{(1 - ratio) * 100:.0f}% below the national average"
    else:
        compare = "close to the national average"
    parts = [
        f"{muni} had {rate:.0f} reported violent offences (all types) per 100,000 residents"
        + (f" ({period})" if period else "")
        + f", {compare} ({national:.0f}). It ranks {rank} of {total} municipalities, where 1 is the highest rate."
    ]
    if label == "unsafe":
        parts.append("It is marked red on the map: plan routes with the safety ranking and stay on busier streets after dark.")
    elif label == "mixed":
        parts.append("It is marked orange on the map: somewhat above average, so check recent reports before walking at night.")
    else:
        parts.append("It is not highlighted on the map.")
    if custom_period:
        parts.append(
            f"In {period} there were {reports} community report(s) in SafeRoute, and {news} crime news "
            "article(s) mentioned the area."
        )
    else:
        parts.append(
            f"In the last 30 days there were {reports} community report(s), and {news} crime news article(s) "
            "mentioned the area in the last 90 days."
        )
    parts.append(
        "This counts every reported violent offence, including minor assaults and threats, so it only compares "
        "Danish areas with each other; internationally Denmark is among the safest countries. Per-resident rates "
        "also make city centres with many visitors look worse than they feel."
    )
    return " ".join(parts)


async def get_crime_index(city: str, from_year: int | None = None, to_year: int | None = None) -> dict:
    """Latest four quarters by default; with ``from_year``/``to_year`` the
    numbers are for that range (yearly averages), fetched on demand."""
    if not zone_cache.get_all():
        raise DataNotLoadedError()
    entry = _resolve(city)
    if entry is None:
        raise CityNotFoundError(city)
    muni = entry.name.title()
    now = datetime.now(UTC)

    if from_year is None and to_year is None:
        info = zone_cache.get_info()
        own = {
            "violent_crimes_per_year": entry.violent_crimes_per_year,
            "population": entry.population,
            "rate_per_100k": entry.crime_rate_per_100k,
            "safety_score": entry.safety_score,
        }
        all_rates = [m.crime_rate_per_100k for m in zones.all_municipalities()]
        national = zones.national_rate_per_100k()
        period_label = info.crime_period if info else None
        reports = _reports_in(entry, now - timedelta(days=30))
        news = _news_in(entry.name, now - timedelta(days=90))
        custom = False
        last_updated = info.fetched_at if info else None
    else:
        from_year = from_year or to_year
        to_year = to_year or from_year
        stats = await periods.stats_for(from_year, to_year)
        own = stats.municipalities.get(entry.name)
        if own is None:
            raise CityNotFoundError(city)
        all_rates = [m["rate_per_100k"] for m in stats.municipalities.values()]
        national = stats.national_rate_per_100k
        period_label = stats.label
        reports = _reports_in(entry, stats.start, stats.end)
        news = _news_in(entry.name, stats.start, stats.end)
        custom = True
        last_updated = now

    rates = sorted(all_rates, reverse=True)
    rank = rates.index(own["rate_per_100k"]) + 1
    lower = sum(1 for r in rates if r < own["rate_per_100k"])
    label = zones.label_for_score(own["safety_score"])

    return {
        "city": _clean(city).title(),
        "municipality": muni,
        "crime_index": round(lower / max(len(rates) - 1, 1) * 100, 1),
        "safety_index": round(own["safety_score"] * 10, 1),
        "safety_label": label,
        "violent_crimes_per_year": own["violent_crimes_per_year"],
        "population": own["population"],
        "rate_per_100k": own["rate_per_100k"],
        "national_rate_per_100k": national,
        "rank": rank,
        "municipalities_ranked": len(rates),
        "recent_reports_30d": reports,
        "recent_news_90d": news,
        "summary": _summary(muni, own["rate_per_100k"], national, rank, len(rates), label,
                            reports, news, period_label, custom_period=custom),
        "data_period": period_label,
        "last_updated": last_updated,
        "from_year": from_year,
        "to_year": to_year,
        "perception": world.find_city(_clean(city), "DK") or world.find_city(muni, "DK"),
        "country": _country_context("DK", from_year, to_year),
    }


def available_periods() -> dict:
    """Year ranges the period filter can offer."""
    info = zone_cache.get_info()
    latest_year = int(info.crime_period.split("-")[-1][:4]) if info and info.crime_period[:4].isdigit() else None
    country_years = world.available_years()
    return {
        "denmark": {"min_year": periods.MIN_YEAR, "max_year": latest_year or datetime.now(UTC).year},
        "countries": {"min_year": country_years[0], "max_year": country_years[1]} if country_years else None,
    }


def _country_context(iso2: str, from_year: int | None = None, to_year: int | None = None) -> dict | None:
    ranking = world.country_ranking(from_year, to_year)
    entry = next((c for c in ranking if c["iso2"] == iso2), None)
    if entry is None and (from_year or to_year):
        # World Bank data lags 2–3 years: for a recent range fall back to the
        # newest year available; homicides_year in the response says which.
        ranking = world.country_ranking()
        entry = next((c for c in ranking if c["iso2"] == iso2), None)
    if entry is None:
        return None
    keys = ("name", "rank", "crime_index", "safety_index", "homicides_per_100k",
            "homicides_year", "crime_in_area_percent", "crime_in_area_year")
    return {
        **{k: entry[k] for k in keys},
        "countries_ranked": len(ranking),
        "eu_crime_in_area_percent": world.eu_average()["crime_in_area_percent"],
    }


def list_cities() -> list[str]:
    return [m.name.title() for m in zones.all_municipalities()]
