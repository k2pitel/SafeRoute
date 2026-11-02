"""Eurostat dissemination API (JSON-stat 2.0) — free, no key.

Free stand-in for the perception data a paid crime index (e.g. Numbeo)
sells, from the EU's own surveys. Reuse is allowed with acknowledgement
("Source: Eurostat"), so the app shows that line wherever these numbers
appear.

- ``urb_percep``  Perception survey on quality of life in European cities:
                  "I feel safe walking alone at night in my city/neighbourhood".
- ``ilc_mddw03``  EU-SILC: share of people reporting crime, violence or
                  vandalism in their area, per country.
"""
import httpx

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}"
TIMEOUT_SECONDS = 60
FETCH_ERRORS = (httpx.HTTPError, KeyError, ValueError, TypeError)

# urb_percep indicator codes (checked against the API, Nov 2026)
NIGHT_CITY = {"PS3514V": "strongly_agree", "PS3515V": "somewhat_agree",
              "PS3516V": "somewhat_disagree", "PS3517V": "strongly_disagree"}
NIGHT_NEIGHBOURHOOD = {"PS3519V": "strongly_agree", "PS3520V": "somewhat_agree",
                       "PS3521V": "somewhat_disagree", "PS3522V": "strongly_disagree"}
# Survey rounds that asked the walking-at-night questions; newest wins per city.
PERCEPTION_YEARS = ("2019", "2023")


def unpack(data: dict) -> dict[tuple[str, ...], float]:
    """JSON-stat 2.0 → {(code per dimension, in data["id"] order): value}.
    Values are stored flat in row-major order over the dimension sizes."""
    ids, sizes = data["id"], data["size"]
    by_position = [
        {pos: code for code, pos in data["dimension"][dim]["category"]["index"].items()} for dim in ids
    ]
    out: dict[tuple[str, ...], float] = {}
    for flat_str, value in data["value"].items():
        flat = int(flat_str)
        positions = []
        for size in reversed(sizes):
            positions.append(flat % size)
            flat //= size
        positions.reverse()
        out[tuple(by_position[i][p] for i, p in enumerate(positions))] = value
    return out


def labels(data: dict, dimension: str) -> dict[str, str]:
    return data["dimension"][dimension]["category"]["label"]


async def _get(client: httpx.AsyncClient, dataset: str, params: list[tuple[str, str]]) -> dict:
    resp = await client.get(BASE_URL.format(dataset=dataset), params=[("format", "JSON"), ("lang", "EN"), *params])
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise ValueError(f"Eurostat {dataset}: {data['error']}")
    return data


async def fetch_city_night_safety(client: httpx.AsyncClient) -> dict[str, dict]:
    """Per city code: name, year and the answer shares (%) for walking alone at
    night in the city and in the neighbourhood. Newest survey round per city."""
    codes = [*NIGHT_CITY, *NIGHT_NEIGHBOURHOOD]
    params = [("indic_ur", c) for c in codes] + [("time", y) for y in PERCEPTION_YEARS]
    data = await _get(client, "urb_percep", params)
    values = unpack(data)
    dims = data["id"]
    i_ind, i_city, i_time = dims.index("indic_ur"), dims.index("cities"), dims.index("time")
    names = labels(data, "cities")

    cities: dict[str, dict] = {}
    for key, value in values.items():
        city, year, indicator = key[i_city], key[i_time], key[i_ind]
        entry = cities.get(city)
        if entry is None or year > entry["year"]:
            entry = cities[city] = {"code": city, "name": names.get(city, city), "year": year, "city": {}, "neighbourhood": {}}
        if year < entry["year"]:
            continue
        if indicator in NIGHT_CITY:
            entry["city"][NIGHT_CITY[indicator]] = value
        else:
            entry["neighbourhood"][NIGHT_NEIGHBOURHOOD[indicator]] = value
    return {code: e for code, e in cities.items() if len(e["city"]) == len(NIGHT_CITY)}


async def fetch_crime_in_area(client: httpx.AsyncClient) -> dict[str, dict]:
    """Per country (ISO 3166 alpha-2, Eurostat style: EL = Greece) plus the
    EU27 aggregate: share of the population reporting crime, violence or
    vandalism in their area, newest year available."""
    data = await _get(client, "ilc_mddw03", [("hhcomp", "TOTAL"), ("rskpovth", "TOTAL"), ("unit", "PC")])
    values = unpack(data)
    dims = data["id"]
    i_geo, i_time = dims.index("geo"), dims.index("time")
    names = labels(data, "geo")
    latest: dict[str, dict] = {}
    for key, value in values.items():
        geo, year = key[i_geo], key[i_time]
        if geo not in latest or year > latest[geo]["year"]:
            latest[geo] = {"geo": geo, "name": names.get(geo, geo), "year": year, "percent": value}
    return latest
