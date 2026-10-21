"""Danish news outlets — RSS feeds and article pages (nyhedskilder, afsnit 4.1).

Returns raw, unfiltered feed entries; deciding what counts as crime news
and where it happened is domain logic and lives in api/news/service.py.
"""
import html as html_module
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

# Danish outlets with free, no-key RSS feeds. Pooling several gives a wider
# current-news snapshot — RSS is inherently "latest ~N items", not a
# historical archive (see datalag/news_archive.py for how history is kept).
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

FEED_TIMEOUT_SECONDS = 10
ARTICLE_TIMEOUT_SECONDS = 10


@dataclass
class FeedEntry:
    source: str
    title: str
    url: str
    published_at: datetime
    description: str = ""
    categories: list[str] = field(default_factory=list)


async def fetch_feed(client: httpx.AsyncClient, source: str, url: str) -> list[FeedEntry]:
    """Every item in one RSS feed. Raises httpx.HTTPError / ParseError on failure."""
    resp = await client.get(url)
    resp.raise_for_status()
    root = ElementTree.fromstring(resp.content)

    entries: list[FeedEntry] = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip().replace("\n", " ")
        link = item.findtext("link")
        if not title or not link:
            continue

        pub_date_raw = item.findtext("pubDate")
        try:
            published_at = parsedate_to_datetime(pub_date_raw) if pub_date_raw else datetime.now(UTC)
        except (TypeError, ValueError):
            published_at = datetime.now(UTC)

        entries.append(
            FeedEntry(
                source=source,
                title=title,
                url=link,
                published_at=published_at,
                description=item.findtext("description") or "",
                categories=[c.text for c in item.findall("category") if c.text],
            )
        )
    return entries


# Strips a fetched article page down to plain text so the place lookup has
# more than just the headline to search — a location the headline doesn't
# name (e.g. "Mand anholdt efter overfald") is very often in the body.
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


async def fetch_article_text(client: httpx.AsyncClient, url: str) -> str:
    """Best-effort plain text of an article's <p> paragraphs. Empty string on
    any failure (dead link, paywall block, timeout, non-HTML, no <p> tags) —
    callers already have the title as a fallback, this is purely additive."""
    try:
        resp = await client.get(
            url,
            timeout=ARTICLE_TIMEOUT_SECONDS,
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
