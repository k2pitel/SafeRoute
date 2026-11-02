"""World Bank Indicators API — free, no key, data under CC BY 4.0.

``VC.IHR.PSRC.P5``: intentional homicides per 100,000 people (UNODC), the
one crime measure comparable across every country — the free hard-number
half of a country crime ranking (Germany and the US included, US-51/52).
"""
import httpx

COUNTRIES_URL = "https://api.worldbank.org/v2/country"
INDICATOR_URL = "https://api.worldbank.org/v2/country/all/indicator/VC.IHR.PSRC.P5"
TIMEOUT_SECONDS = 60
FETCH_ERRORS = (httpx.HTTPError, KeyError, ValueError, TypeError, IndexError)


async def _pages(client: httpx.AsyncClient, url: str, params: dict) -> list[dict]:
    rows, page = [], 1
    while True:
        resp = await client.get(url, params={**params, "format": "json", "per_page": 400, "page": page})
        resp.raise_for_status()
        meta, data = resp.json()
        rows.extend(data or [])
        if page >= int(meta["pages"]):
            return rows
        page += 1


async def fetch_homicide_rates(client: httpx.AsyncClient) -> dict[str, dict]:
    """Per ISO2 country code: name, iso3, year and homicides per 100,000 —
    the most recent non-empty value. Regional aggregates are dropped."""
    countries = {
        c["id"]: c
        for c in await _pages(client, COUNTRIES_URL, {})
        if c.get("region", {}).get("id") not in (None, "NA")  # "NA" = aggregate (World, EU, ...)
    }
    rows = await _pages(client, INDICATOR_URL, {"mrnev": 1})
    rates: dict[str, dict] = {}
    for row in rows:
        iso3 = row.get("countryiso3code")
        if iso3 not in countries or row.get("value") is None:
            continue
        country = countries[iso3]
        rates[country["iso2Code"]] = {
            "iso2": country["iso2Code"],
            "iso3": iso3,
            "name": country["name"],
            "region": country["region"]["value"].strip(),
            "year": row["date"],
            "homicides_per_100k": round(float(row["value"]), 2),
        }
    return rates
