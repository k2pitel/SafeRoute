# OSRM Routing Setup (self-hosted, figur 4.3)

SafeRoute uses [OSRM](https://project-osrm.org/) only for route geometry and
walking time. The safety layer sits on top, in the backend: OSRM returns
candidate routes, and `backend/app/api/routes/service.py` attaches a
tryghedsscore and explanation to each one. All HTTP calls to OSRM go through
`backend/app/external/osrm.py`. OSRM itself never holds SafeRoute logic.

## Preparing a pedestrian graph (example: Denmark)

The compose file mounts `infrastructure/osrm-data/` (git-ignored) into the
container at `/data`, so build the graph there:

```bash
mkdir -p infrastructure/osrm-data && cd infrastructure/osrm-data

# 1. Download an OSM extract (Geofabrik)
curl -L https://download.geofabrik.de/europe/denmark-latest.osm.pbf -o map.osm.pbf

# 2. Extract with the foot profile
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-extract -p /opt/foot.lua /data/map.osm.pbf

# 3. Partition + customize (MLD algorithm)
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-partition /data/map.osrm
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-customize /data/map.osrm
```

Then start it, either through compose (`osrm` service in
`infrastructure/docker-compose.yml`) or standalone:

```bash
docker run -t -i -p 5000:5000 -v "${PWD}:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/map.osrm
```

## Pointing the backend at it

Set `OSRM_SERVER_URL=http://localhost:5000` in `backend/.env`. The default in
`.env.example` is the public demo instance (`routing.openstreetmap.de`), which
is fine for development but rate-limits under load. Inside docker compose,
the backend is already wired to `http://osrm:5000`.

The backend asks for `alternatives=true`, so it can offer a "fastest" and a
"safest" option (Route panel wireframe). If OSRM does not answer within 3 s,
the backend falls back to a straight-line estimate (NF7).
