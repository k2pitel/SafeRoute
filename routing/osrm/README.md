# OSRM Routing Setup

SafeRoute uses [OSRM](https://project-osrm.org/) for the base pedestrian
routing graph. The safety-scoring layer sits on top: OSRM returns raw
candidate route geometries, and the backend annotates/re-ranks them using
`segment_scores` (see `ml/serving.py` + `backend/app/routers/routes.py`).

## Preparing a city extract (example: Aarhus, Denmark)

```bash
# 1. Download an OSM extract for your region (e.g. from Geofabrik)
wget https://download.geofabrik.de/europe/denmark-latest.osm.pbf -O map.osm.pbf

# 2. Extract using the foot/pedestrian profile
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-extract -p /opt/foot.lua /data/map.osm.pbf

# 3. Partition + customize (for MLD algorithm)
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-partition /data/map.osrm
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-customize /data/map.osrm

# 4. Run the routing server
docker run -t -i -p 5000:5000 -v "${PWD}:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/map.osrm
```

Set `OSRM_SERVER_URL=http://localhost:5000` in `backend/.env` to point the
backend at this server (already the default in `.env.example`).

## Python bindings

The backend calls OSRM over its HTTP API (no special client library
required) via `httpx`, e.g.:

```python
import httpx

async def get_osrm_route(lat1, lon1, lat2, lon2):
    url = f"{OSRM_SERVER_URL}/route/v1/foot/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "full", "geometries": "geojson", "alternatives": "true"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        return resp.json()
```

Multiple alternative routes (`alternatives=true`) are what let the backend
compare a "fastest" vs. "safest" option, matching the Route page wireframe.
