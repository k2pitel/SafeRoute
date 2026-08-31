"""GET /api/news — latest crime-related news for Denmark (optionally city-filtered)."""
import asyncio
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx
from fastapi import APIRouter, BackgroundTasks, Query

from app import news_archive
from app.schemas import NewsItem

router = APIRouter(prefix="/api/news", tags=["news"])

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

# Approximate city/town centers, used to pin a headline on the map when it
# names one — the feeds themselves carry no geodata, so this is always a
# "which town" approximation, never the actual crime scene. Covers the
# ~70 largest Danish towns; still not exhaustive of every municipality.
DANISH_PLACES = {
    "københavn": (55.6761, 12.5683),
    "copenhagen": (55.6761, 12.5683),
    "frederiksberg": (55.6786, 12.5306),
    "aarhus": (56.1629, 10.2039),
    "århus": (56.1629, 10.2039),
    "odense": (55.4038, 10.4024),
    "aalborg": (57.0488, 9.9217),
    "esbjerg": (55.4765, 8.4594),
    "randers": (56.4607, 10.0369),
    "kolding": (55.4904, 9.4721),
    "horsens": (55.8607, 9.8503),
    "vejle": (55.7091, 9.5357),
    "roskilde": (55.6415, 12.0803),
    "herning": (56.1362, 8.9761),
    "silkeborg": (56.1697, 9.5459),
    "næstved": (55.2299, 11.7607),
    "fredericia": (55.5654, 9.7526),
    "viborg": (56.4530, 9.4020),
    "køge": (55.4578, 12.1817),
    "holstebro": (56.3606, 8.6153),
    "taastrup": (55.6500, 12.3000),
    "slagelse": (55.4055, 11.3547),
    "hillerød": (55.9268, 12.3072),
    "sønderborg": (54.9092, 9.7906),
    "svendborg": (55.0577, 10.6106),
    "hjørring": (57.4649, 9.9799),
    "holbæk": (55.7178, 11.7095),
    "frederikshavn": (57.4407, 10.5372),
    "nørresundby": (57.0693, 9.9217),
    "ringsted": (55.4419, 11.7909),
    "skive": (56.5661, 9.0287),
    "haderslev": (55.2500, 9.4900),
    "nykøbing falster": (54.9667, 11.8750),
    "nykøbing mors": (56.7929, 8.8517),
    "helsingør": (56.0361, 12.6136),
    "aabenraa": (55.0442, 9.4197),
    "ballerup": (55.7308, 12.3608),
    "ishøj": (55.6167, 12.3500),
    "brøndby": (55.6500, 12.4167),
    "glostrup": (55.6667, 12.4000),
    "gladsaxe": (55.7333, 12.4667),
    "lyngby": (55.7700, 12.5000),
    "hvidovre": (55.6500, 12.4833),
    "rødovre": (55.6833, 12.4500),
    "greve": (55.5833, 12.3000),
    "solrød": (55.5333, 12.1833),
    "vallensbæk": (55.6167, 12.3667),
    "albertslund": (55.6600, 12.3600),
    "farum": (55.8100, 12.3600),
    "værløse": (55.7833, 12.3500),
    "birkerød": (55.8400, 12.4300),
    "hørsholm": (55.8833, 12.4833),
    "rungsted": (55.9000, 12.5500),
    "kalundborg": (55.6797, 11.0894),
    "korsør": (55.3300, 11.1400),
    "nykøbing sjælland": (55.9167, 11.6667),
    "nakskov": (54.8300, 11.1400),
    "maribo": (54.7719, 11.5083),
    "faaborg": (55.1017, 10.2417),
    "middelfart": (55.5061, 9.7367),
    "assens": (55.2700, 9.9000),
    "nyborg": (55.3128, 10.7889),
    "ringe": (55.2333, 10.4833),
    "grenaa": (56.4133, 10.8794),
    "ebeltoft": (56.1958, 10.6817),
    "hobro": (56.6389, 9.7972),
    "skagen": (57.7208, 10.5836),
    "brønderslev": (57.2667, 9.9500),
    "thisted": (56.9553, 8.6939),
    "struer": (56.4894, 8.6011),
    "lemvig": (56.5461, 8.3050),
    "ikast": (56.1394, 9.1553),
    "brande": (55.9333, 9.1333),
    "tønder": (54.9358, 8.8619),
    "ribe": (55.3306, 8.7647),
    "varde": (55.6211, 8.4814),
    "rønne": (55.1000, 14.7000),
}

# word-boundary regex per place name (compiled once), so e.g. "ry" doesn't
# match inside an unrelated word.
_PLACE_PATTERNS = [(name, coords, re.compile(rf"\b{re.escape(name)}\b")) for name, coords in DANISH_PLACES.items()]


def _find_location(*texts: str) -> tuple[float | None, float | None]:
    combined = " ".join(t for t in texts if t).lower()
    for _name, coords, pattern in _PLACE_PATTERNS:
        if pattern.search(combined):
            return coords
    return None, None


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


async def poll_and_archive_once() -> int:
    """Called by the background poller in main.py's lifespan. Returns new-item count."""
    items = await pool_live_feeds()
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
    from app import news_backfill  # local import: avoids a circular import with news.py at module load

    background_tasks.add_task(news_backfill.run_backfill)
    return {"status": "started", "note": "poll GET /api/news/archive-status for progress"}
