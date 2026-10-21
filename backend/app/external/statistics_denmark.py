"""Danmarks Statistik (StatBank API) + open DAGI municipality boundaries.

Official Danish crime data has no per-incident coordinates, only counts per
municipality — which is exactly what a zone polygon needs.
"""
import csv
import io

import httpx

STATBANK_TABLEINFO_URL = "https://api.statbank.dk/v1/tableinfo/{table}"
STATBANK_DATA_URL = "https://api.statbank.dk/v1/data"
MUNICIPALITY_BOUNDARIES_URL = "https://raw.githubusercontent.com/Neogeografen/dagi/master/geojson/kommuner.geojson"

VIOLENT_CRIME_CODE = "12"  # STRAF11 "Voldsforbrydelser i alt" (violent crimes, total)
QUARTERS_TO_SUM = 4  # trailing year, so small municipalities aren't just quarterly noise
TIMEOUT_SECONDS = 30

# What the fetchers below raise on a network or response-shape problem.
FETCH_ERRORS = (httpx.HTTPError, KeyError, StopIteration)


def normalize_name(name: str) -> str:
    """Join key between StatBank rows and boundary features."""
    return name.strip().lower().replace("-", " ")


async def _latest_quarters(client: httpx.AsyncClient, table: str, n: int) -> list[str]:
    resp = await client.get(STATBANK_TABLEINFO_URL.format(table=table))
    resp.raise_for_status()
    time_var = next(v for v in resp.json()["variables"] if v["id"] == "Tid")
    return [v["id"] for v in time_var["values"][-n:]]


async def _fetch_csv(client: httpx.AsyncClient, table: str, variables: list[dict]) -> list[dict]:
    resp = await client.post(STATBANK_DATA_URL, json={"table": table, "format": "CSV", "variables": variables})
    resp.raise_for_status()
    text = resp.content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text), delimiter=";"))


async def fetch_violent_crime_by_area(client: httpx.AsyncClient) -> dict[str, float]:
    """STRAF11, code 12, summed over the latest four quarters, per area."""
    quarters = await _latest_quarters(client, "STRAF11", QUARTERS_TO_SUM)
    rows = await _fetch_csv(
        client,
        "STRAF11",
        [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "OVERTRÆD", "values": [VIOLENT_CRIME_CODE]},
            {"code": "Tid", "values": quarters},
        ],
    )
    totals: dict[str, float] = {}
    for row in rows:
        name = normalize_name(row["OMRÅDE"])
        try:
            value = float(row["INDHOLD"])
        except ValueError:
            continue
        totals[name] = totals.get(name, 0) + value
    return totals


async def fetch_population_by_area(client: httpx.AsyncClient) -> dict[str, int]:
    """FOLK1A, latest quarter, total population per area."""
    quarters = await _latest_quarters(client, "FOLK1A", 1)
    rows = await _fetch_csv(
        client,
        "FOLK1A",
        [
            {"code": "OMRÅDE", "values": ["*"]},
            {"code": "KØN", "values": ["TOT"]},
            {"code": "ALDER", "values": ["IALT"]},
            {"code": "CIVILSTAND", "values": ["TOT"]},
            {"code": "Tid", "values": quarters},
        ],
    )
    populations: dict[str, int] = {}
    for row in rows:
        name = normalize_name(row["OMRÅDE"])
        try:
            populations[name] = int(float(row["INDHOLD"]))
        except ValueError:
            continue
    return populations


async def fetch_municipality_boundaries(client: httpx.AsyncClient) -> dict[str, list[dict]]:
    """GeoJSON geometries per municipality — a list, since municipalities with
    islands/exclaves come back as several separate features."""
    resp = await client.get(MUNICIPALITY_BOUNDARIES_URL)
    resp.raise_for_status()
    geojson = resp.json()

    boundaries: dict[str, list[dict]] = {}
    for feature in geojson["features"]:
        name = normalize_name(feature["properties"]["KOMNAVN"])
        boundaries.setdefault(name, []).append(feature["geometry"])
    return boundaries
