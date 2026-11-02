"""Bytryghedsoversigt (F4) from real data (US-29).

Everything comes from sources the system already has: the municipality's
violent-crime rate (Danmarks Statistik, via the zone cache), its rank
nationally, community reports in it from the last 30 days and placed crime
news from the last 90 days. The summary is generated from those numbers —
no invented survey figures or contributor counts.
"""
from datetime import UTC, datetime, timedelta

from app.api.crime_index import world
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


def _reports_in(entry, since: datetime) -> int:
    box = entry.bbox
    rows = local_store.list_reports(box.min_lon, box.min_lat, box.max_lon, box.max_lat, limit=1000, since=since)
    return sum(1 for r in rows if zones.municipality_at(r["latitude"], r["longitude"]) is entry)


def _news_in(name: str, since: datetime) -> int:
    count = 0
    for item in news_archive.load_items(limit=5000):
        published = item.published_at if item.published_at.tzinfo else item.published_at.replace(tzinfo=UTC)
        if published < since:
            break  # newest first
        if matches_city(name, item.title, item.latitude, item.longitude):
            count += 1
    return count


def _summary(muni: str, rate: float, national: float, rank: int, total: int, label: str,
             reports: int, news: int, period: str | None) -> str:
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


def get_crime_index(city: str) -> dict:
    if not zone_cache.get_all():
        raise DataNotLoadedError()
    entry = _resolve(city)
    if entry is None:
        raise CityNotFoundError(city)

    municipalities = zones.all_municipalities()
    rates = sorted((m.crime_rate_per_100k for m in municipalities), reverse=True)
    rank = rates.index(entry.crime_rate_per_100k) + 1
    lower = sum(1 for r in rates if r < entry.crime_rate_per_100k)
    national = zones.national_rate_per_100k()
    label = zones.label_for_score(entry.safety_score)
    now = datetime.now(UTC)
    reports = _reports_in(entry, now - timedelta(days=30))
    news = _news_in(entry.name, now - timedelta(days=90))
    info = zone_cache.get_info()
    muni = entry.name.title()

    return {
        "city": _clean(city).title(),
        "municipality": muni,
        "crime_index": round(lower / max(len(rates) - 1, 1) * 100, 1),
        "safety_index": round(entry.safety_score * 10, 1),
        "safety_label": label,
        "violent_crimes_per_year": entry.violent_crimes_per_year,
        "population": entry.population,
        "rate_per_100k": entry.crime_rate_per_100k,
        "national_rate_per_100k": national,
        "rank": rank,
        "municipalities_ranked": len(rates),
        "recent_reports_30d": reports,
        "recent_news_90d": news,
        "summary": _summary(muni, entry.crime_rate_per_100k, national, rank, len(rates), label,
                            reports, news, info.crime_period if info else None),
        "data_period": info.crime_period if info else None,
        "last_updated": info.fetched_at if info else None,
        "perception": world.find_city(_clean(city), "DK") or world.find_city(muni, "DK"),
        "country": _country_context("DK"),
    }


def _country_context(iso2: str) -> dict | None:
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
