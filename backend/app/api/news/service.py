"""Crime news feed (F9) — filtering, placing and archiving news items.

Shared by both callers named in afsnit 5.2.1.1: the Async Worker runs
``poll_and_archive_once`` every 15 minutes (worker/jobs.py), and
GET /api/news calls ``get_news``, which merges a live fetch with the archive.
"""
import asyncio

import httpx

from app.api.news.places import find_location
from app.datalag import news_archive
from app.external import news_sources
from app.shared.news import NewsItem

CRIME_KEYWORDS = [
    "kriminalitet", "indbrud", "overfald", "røveri", "vold", "drab", "mord",
    "anholdt", "sigtet", "fængsel", "dømt", "politiet", "skudt", "skyderi",
    "knivstukket", "voldtægt", "tyveri", "bandekriminalitet", "efterlyst",
    "varetægtsfængsl", "svindel", "trusler", "chikane", "narko", "krimi",
]

# Outlet-provided category names that mean "crime" even when the headline
# itself doesn't contain one of the keywords above (e.g. Ekstra Bladet
# tags its crime desk articles "Krimi").
CRIME_CATEGORIES = {"krimi", "retssager", "retssag"}

LATEST_LIMIT = 200
YEAR_LIMIT = 500


def is_crime_related(title: str, categories: list[str]) -> bool:
    lowered = title.lower()
    if any(keyword in lowered for keyword in CRIME_KEYWORDS):
        return True
    return any(cat.strip().lower() in CRIME_CATEGORIES for cat in categories)


def normalize_city(city: str | None) -> str | None:
    """'Aarhus, Denmark' -> 'aarhus'; whole-country values -> None (no filter)."""
    if city and city.strip().lower() not in ("", "denmark", "danmark", "all"):
        return city.strip().lower().split(",")[0].strip()
    return None


def _to_news_item(entry: news_sources.FeedEntry) -> NewsItem:
    lat, lon = find_location(entry.title, entry.description)
    return NewsItem(
        title=entry.title,
        url=entry.url,
        source=entry.source,
        published_at=entry.published_at,
        latitude=lat,
        longitude=lon,
    )


async def pool_live_feeds() -> list[NewsItem]:
    """Every configured feed right now, crime items only, deduped by URL.

    Feeds are fetched in parallel with return_exceptions=True, so one
    unreachable outlet only removes its own items (NF7).
    """
    async with httpx.AsyncClient(timeout=news_sources.FEED_TIMEOUT_SECONDS) as client:
        results = await asyncio.gather(
            *(news_sources.fetch_feed(client, source, url) for source, url in news_sources.FEEDS),
            return_exceptions=True,
        )

    items: list[NewsItem] = []
    seen_urls: set[str] = set()
    for result in results:
        if isinstance(result, Exception):
            continue
        for entry in result:
            if entry.url in seen_urls or not is_crime_related(entry.title, entry.categories):
                continue
            seen_urls.add(entry.url)
            items.append(_to_news_item(entry))
    return items


async def _enrich_unlocated(items: list[NewsItem]) -> None:
    """For items the title/description couldn't place, fetch the article's
    <p> text and try again — mutates items in place. Only called from the
    archiving path (a handful of new items per poll), never from the
    interactive GET /api/news, so the user never waits on it."""
    unlocated = [item for item in items if item.latitude is None]
    if not unlocated:
        return
    async with httpx.AsyncClient() as client:
        texts = await asyncio.gather(*(news_sources.fetch_article_text(client, item.url) for item in unlocated))
    for item, text in zip(unlocated, texts):
        if not text:
            continue
        lat, lon = find_location(item.title, text)
        if lat is not None:
            item.latitude, item.longitude = lat, lon


async def poll_and_archive_once() -> int:
    """One polling round: fetch, place, archive. Returns the new-item count."""
    items = await pool_live_feeds()
    await _enrich_unlocated(items)
    return news_archive.save_items(items)


async def get_news(city: str | None = None, year: int | None = None) -> list[NewsItem]:
    """
    Without ``year``: live feeds merged with the archive, newest first —
    what the News tab uses day-to-day.

    With ``year``: archived items from just that year, skipping the live
    fetch entirely (a live feed has nothing to say about 2020). The archive
    is seeded by the Async Worker's poller and, for pre-launch years, by the
    one-time backfill (api/news/backfill.py).
    """
    city_filter = normalize_city(city)

    if year is not None:
        items = news_archive.load_items(city_filter=city_filter, year=year, limit=YEAR_LIMIT)
        items.sort(key=lambda i: i.published_at, reverse=True)
        return items

    live_items = await pool_live_feeds()
    archived_items = news_archive.load_items(city_filter=None)  # filter after merge, below

    items: list[NewsItem] = []
    seen: set[str] = set()
    for item in [*live_items, *archived_items]:
        dedupe_key = item.url if item.url else item.title.lower()
        title_key = item.title.strip().lower()
        if dedupe_key in seen or title_key in seen:
            continue
        if city_filter and city_filter not in item.title.lower():
            continue
        seen.add(dedupe_key)
        seen.add(title_key)
        items.append(item)

    items.sort(key=lambda i: i.published_at, reverse=True)
    return items[:LATEST_LIMIT]


def archived_count() -> int:
    return news_archive.count()
