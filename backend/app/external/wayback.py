"""Internet Archive Wayback Machine — CDX index queries.

Only the archive's own metadata (original URL + crawl timestamp) is read;
article bodies are never fetched or stored.
"""
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

CDX_URL = "https://web.archive.org/cdx/search/cdx"
TIMEOUT_SECONDS = 45


@dataclass
class ArchivedUrl:
    url: str
    crawled_at: datetime


def _parse_cdx_timestamp(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=UTC)


async def fetch_archived_urls(
    client: httpx.AsyncClient, pattern: str, date_from: str, date_to: str, limit: int
) -> list[ArchivedUrl]:
    """Unique URLs matching ``pattern`` crawled between two YYYYMMDD dates.
    Raises httpx.HTTPError (incl. timeouts) on failure."""
    resp = await client.get(
        CDX_URL,
        params={
            "url": pattern,
            "output": "json",
            "from": date_from,
            "to": date_to,
            "filter": "statuscode:200",
            "collapse": "urlkey",
            "limit": str(limit),
        },
    )
    resp.raise_for_status()
    rows = resp.json()
    if not rows or len(rows) < 2:
        return []

    header = rows[0]
    url_idx, ts_idx = header.index("original"), header.index("timestamp")
    return [ArchivedUrl(url=row[url_idx], crawled_at=_parse_cdx_timestamp(row[ts_idx])) for row in rows[1:]]
