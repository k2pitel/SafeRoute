"""One-time historical backfill via the Internet Archive's Wayback Machine.

Different from the live RSS poller (news.py / news_archive.py): this
doesn't scrape any publisher directly. It queries the Wayback Machine's
public CDX index — a legitimate, purpose-built archive service — for URLs
it already crawled from a given outlet's crime section in the past, and
derives a title from each URL's own slug (e.g.
".../12-aars-faengsel-for-planer-om-terrorangreb-i-koebenhavn/..." reads
as a headline on its own). It does NOT fetch or store article bodies from
either the live site or the archived snapshot — just the URL, its slug,
and when Wayback saw it. That keeps this well inside "using a public
archive's own metadata," short of republishing anyone's content.

Coverage is uneven across outlets (see the SOURCES comment below) — this
backfills what's actually reliably available, not a promise of completeness.
"""
import logging
import re
from datetime import datetime, timezone

import httpx

from app.danish_places import find_location as _find_location
from app.routers.news import _is_crime_related
from app.schemas import NewsItem
from app.services import news_archive

logger = logging.getLogger("saferoute.news_backfill")

CDX_URL = "https://web.archive.org/cdx/search/cdx"

# Only outlets confirmed to have a dedicated, slug-URL crime section with
# workable Wayback coverage (checked manually) — TV2's regional sites
# timed out on CDX queries and Politiken's URL pattern didn't match
# anything, so they're left out rather than silently returning nothing.
SOURCES = [
    ("Ekstra Bladet", "ekstrabladet.dk/krimi/*"),
]

# CDX queries against a full multi-year range time out server-side; asking
# per-year keeps each request fast and is also just more polite to a free
# public service than one giant query.
YEAR_RANGE = range(2020, datetime.now(timezone.utc).year + 1)
MAX_ITEMS_PER_YEAR = 500

_ID_ONLY_SLUG = re.compile(r"^(article\d+|\d+)(\.ece)?$")


def _slug_to_title(url: str) -> str | None:
    slug = url.rstrip("/").rsplit("/", 2)[-2] if url.count("/") > 3 else url.rstrip("/").split("/")[-1]
    slug = slug.split("?")[0]
    if not slug or _ID_ONLY_SLUG.match(slug):
        return None  # old CMS URLs like "article4002438.ece" carry no readable title
    words = slug.replace(".ece", "").split("-")
    if len(words) < 3:
        return None  # too short to be a real headline slug
    title = " ".join(words)
    return title[0].upper() + title[1:] if title else None


def _parse_cdx_timestamp(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)


async def _fetch_range(client: httpx.AsyncClient, source: str, pattern: str, date_from: str, date_to: str) -> list[NewsItem]:
    resp = await client.get(
        CDX_URL,
        params={
            "url": pattern,
            "output": "json",
            "from": date_from,
            "to": date_to,
            "filter": "statuscode:200",
            "collapse": "urlkey",
            "limit": str(MAX_ITEMS_PER_YEAR),
        },
    )
    resp.raise_for_status()
    rows = resp.json()
    if not rows or len(rows) < 2:
        return []

    header = rows[0]
    url_idx, ts_idx = header.index("original"), header.index("timestamp")

    items = []
    for row in rows[1:]:
        url, timestamp = row[url_idx], row[ts_idx]
        title = _slug_to_title(url)
        if not title or not _is_crime_related(title, categories=["krimi"]):
            continue
        lat, lon = _find_location(title)
        items.append(
            NewsItem(
                title=title,
                url=url,
                source=f"{source} (archive)",
                published_at=_parse_cdx_timestamp(timestamp),
                latitude=lat,
                longitude=lon,
            )
        )
    return items


# (from, to) pairs for a whole year and, as a fallback, its four quarters —
# CDX queries over a year with a lot of archived pages can be too slow for a
# single request, so a year that times out gets retried in smaller chunks
# rather than being skipped entirely.
def _quarters(year: int) -> list[tuple[str, str]]:
    return [
        (f"{year}0101", f"{year}0331"),
        (f"{year}0401", f"{year}0630"),
        (f"{year}0701", f"{year}0930"),
        (f"{year}1001", f"{year}1231"),
    ]


async def _fetch_year_resilient(client: httpx.AsyncClient, source: str, pattern: str, year: int) -> list[NewsItem]:
    try:
        return await _fetch_range(client, source, pattern, f"{year}0101", f"{year}1231")
    except httpx.HTTPError as exc:
        logger.warning("news_backfill: %s %d timed out as a whole year (%s), retrying by quarter", source, year, exc)

    items: list[NewsItem] = []
    for date_from, date_to in _quarters(year):
        try:
            items.extend(await _fetch_range(client, source, pattern, date_from, date_to))
        except httpx.HTTPError as exc:
            logger.warning("news_backfill: %s %s-%s failed (%s), skipping that quarter", source, date_from, date_to, exc)
    return items


async def run_backfill() -> int:
    """Fetches + archives everything available, year by year. Returns new-item count."""
    total_new = 0
    async with httpx.AsyncClient(timeout=45) as client:
        for source, pattern in SOURCES:
            for year in YEAR_RANGE:
                items = await _fetch_year_resilient(client, source, pattern, year)
                new_count = news_archive.save_items(items)
                total_new += new_count
                logger.warning("news_backfill: %s %d — %d found, %d new", source, year, len(items), new_count)
    return total_new
