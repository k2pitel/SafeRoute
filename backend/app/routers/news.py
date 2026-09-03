"""GET /api/news — latest crime-related news for Denmark (optionally city-filtered)."""
import asyncio
import html as html_module
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx
from fastapi import APIRouter, BackgroundTasks, Query

from app.danish_places import find_location as _find_location
from app.schemas import NewsItem
from app.services import news_archive

router = APIRouter(prefix="/api/news", tags=["news"])

# Strips a fetched article page down to plain text so _find_location has more
# than just the headline to search — a location the headline doesn't name
# (e.g. "Mand anholdt efter overfald") is very often in the article body.
#
# Only <p> tag content is used, not the whole page: nav menus, cookie
# banners, footers, and "related articles" widgets are real text too, and
# they reliably mention *some* Danish city (a footer copyright line, another
# story's teaser, etc.) — searching the whole page produces confident-looking
# but wrong matches from that surrounding chrome rather than the story
# itself. Real prose is reliably wrapped in <p> in practice; nav/menu items
# are not, so this is a cheap, dependency-free way to isolate the story body.
_SCRIPT_STYLE_RE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_P_TAG_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")


async def _fetch_article_text(client: httpx.AsyncClient, url: str) -> str:
    """Best-effort plain-text of an article's <p> paragraphs. Empty string on
    any failure (dead link, paywall block, timeout, non-HTML, no <p> tags
    found) — callers already have the title as a fallback, this is purely
    additive."""
    try:
        resp = await client.get(
            url,
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SafeRouteNewsBot/1.0)"},
        )
        resp.raise_for_status()
        raw = resp.text
    except (httpx.HTTPError, UnicodeDecodeError):
        return ""
    cleaned = _SCRIPT_STYLE_RE.sub(" ", raw)
    paragraphs = _P_TAG_RE.findall(cleaned)
    text = " ".join(_TAG_RE.sub(" ", p) for p in paragraphs)
    return html_module.unescape(text)

# Danish outlets with free, no-key RSS feeds. Pooling several gives a wider
# current-news snapshot — RSS is inherently "latest ~N items", not a
# historical archive (see README > Data Sources: a real deployment would
# use a proper news API/archive for that).
#
# The TV2 regional stations are genuinely local (each covers one part of
# the country), which is as close as free/no-key sources get to "every
# town" — true town-by-town coverage would mean chasing dozens of small,
# often-paywalled local papers instead. TV2 Midtvest (West/Central
# Jutland) has no reachable feed, so that pocket isn't covered here.
FEEDS = [
    ("DR Nyheder", "https://www.dr.dk/nyheder/service/feeds/allenyheder"),
    ("Ekstra Bladet", "https://ekstrabladet.dk/rssfeed/all/"),
    ("Politiken", "https://politiken.dk/rss/senestenyt.rss"),
    ("Berlingske", "https://www.berlingske.dk/content/rss"),
    ("TV2 Nord", "https://www.tv2nord.dk/rss"),  # North Jutland
    ("TV2 Østjylland", "https://www.tv2ostjylland.dk/rss"),  # East Jutland (Aarhus area)
    ("TV2 Fyn", "https://www.tv2fyn.dk/rss"),  # Funen
    ("TV2 Lorry", "https://www.tv2lorry.dk/rss"),  # Greater Copenhagen
    ("TV2 Syd", "https://www.tv2syd.dk/rss"),  # South Jutland
    ("TV2 Øst", "https://www.tv2east.dk/rss"),  # Zealand
    ("TV2 Bornholm", "https://www.tv2bornholm.dk/rss"),
]

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

def _is_crime_related(title: str, categories: list[str]) -> bool:
    lowered = title.lower()
    if any(keyword in lowered for keyword in CRIME_KEYWORDS):
        return True
    return any(cat.strip().lower() in CRIME_CATEGORIES for cat in categories)


async def _fetch_feed(client: httpx.AsyncClient, source: str, url: str) -> list[NewsItem]:
    resp = await client.get(url)
    resp.raise_for_status()
    root = ElementTree.fromstring(resp.content)

    items: list[NewsItem] = []
    for entry in root.findall("./channel/item"):
        title = (entry.findtext("title") or "").strip().replace("\n", " ")
        link = entry.findtext("link")
        if not title or not link:
            continue

        categories = [c.text for c in entry.findall("category") if c.text]
        if not _is_crime_related(title, categories):
            continue

        pub_date_raw = entry.findtext("pubDate")
        try:
            published_at = parsedate_to_datetime(pub_date_raw) if pub_date_raw else datetime.now(timezone.utc)
        except (TypeError, ValueError):
            published_at = datetime.now(timezone.utc)

        description = entry.findtext("description") or ""
        lat, lon = _find_location(title, description)
        items.append(
            NewsItem(
                title=title,
                url=link,
                source=source,
                published_at=published_at,
                latitude=lat,
                longitude=lon,
            )
        )
    return items


def _normalize_city(city: str | None) -> str | None:
    if city and city.strip().lower() not in ("", "denmark", "danmark", "all"):
        return city.strip().lower().split(",")[0].strip()
    return None


async def pool_live_feeds() -> list[NewsItem]:
    """Fetches + filters every configured feed right now. No archive, no dedup-by-title."""
    async with httpx.AsyncClient(timeout=10) as client:
        results = await asyncio.gather(
            *(_fetch_feed(client, source, url) for source, url in FEEDS),
            return_exceptions=True,
        )

    items: list[NewsItem] = []
    seen_urls: set[str] = set()
    for result in results:
        if isinstance(result, Exception):
            continue
        for item in result:
            if item.url in seen_urls:
                continue
            seen_urls.add(item.url)
            items.append(item)
    return items


async def _enrich_unlocated(items: list[NewsItem]) -> None:
    """For items the title/description couldn't place, fetch the actual
    article page and try again — mutates items in place. Only called from
    the archiving path (a handful of new items per poll), never from the
    interactive live-fetch path, so it doesn't slow down the app."""
    unlocated = [item for item in items if item.latitude is None]
    if not unlocated:
        return
    async with httpx.AsyncClient() as client:
        texts = await asyncio.gather(*(_fetch_article_text(client, item.url) for item in unlocated))
    for item, text in zip(unlocated, texts):
        if not text:
            continue
        lat, lon = _find_location(item.title, text)
        if lat is not None:
            item.latitude, item.longitude = lat, lon


async def poll_and_archive_once() -> int:
    """Called by the background poller in main.py's lifespan. Returns new-item count."""
    items = await pool_live_feeds()
    await _enrich_unlocated(items)
    return news_archive.save_items(items)


@router.get("", response_model=list[NewsItem])
async def get_news(
    city: str = Query(None, description="Optional city filter; omit for all of Denmark"),
    year: int = Query(None, description="Optional year filter (e.g. 2020) — pulls from the archive only, not live feeds"),
):
    """
    Default (no `year`): merges the local archive with a fresh live fetch,
    so results are "whatever's live right now" plus recently-archived
    items — this is what the News tab uses day-to-day.

    With `year`: returns archived items from just that year, skipping the
    live fetch entirely (a live feed has nothing to say about 2020). The
    archive itself is seeded two ways — see main.py's lifespan for the
    ongoing poller, and app/news_backfill.py (POST /api/news/backfill) for
    the one-time historical import from the Wayback Machine, which is
    what actually put pre-2026 items in here in the first place.
    """
    city_filter = _normalize_city(city)

    if year is not None:
        items = news_archive.load_items(city_filter=city_filter, year=year, limit=500)
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
    return items[:200]


@router.get("/archive-status")
def archive_status():
    """How many crime items the background poller has archived so far."""
    return {"archived_count": news_archive.count()}


@router.post("/backfill")
async def trigger_backfill(background_tasks: BackgroundTasks):
    """
    Kicks off a one-time historical backfill from the Wayback Machine (see
    app/news_backfill.py) — runs in the background since it makes several
    sequential requests to a free public archive and can take a minute or
    so. Poll /api/news/archive-status to watch the count grow.
    """
    from app.services import news_backfill  # local import: avoids a circular import with news.py at module load

    background_tasks.add_task(news_backfill.run_backfill)
    return {"status": "started", "note": "poll GET /api/news/archive-status for progress"}
