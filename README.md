# SafeRoute

Safety-aware pedestrian navigation: route suggestions with a travel time
**and** a tryghedsscore, colour-coded crime zones, community incident
reports with peer verification, a crime-news feed and walk-time alerts.

Bachelor project (Aarhus University). The report in
`docs/report/` is the source of truth for requirements and architecture;
[`docs/architecture.md`](docs/architecture.md) maps it onto this code.

## Architecture in one picture

Four subsystems (report figur 4.2):

```
 Mobile Client (React Native/Expo)          OS notifications (local, F5)
        │  REST/JSON + Bearer token   ▲ WS /ws/zones
        ▼                             │
 Backend API (FastAPI) ───────────────┘──── OSRM (geometry + time only)
        │        ▲ submit_recalculation()
        │        │
        │   Async Worker (in-process by default; Celery optional)
        │        │  periodic: news 15 min, crime stats 6 h, scores 15 min
        ▼        ▼
     Datalag: SQLite stores + zone cache (dev)  →  PostgreSQL/PostGIS (target)
```

- The **Backend API** answers every client request. The routing service takes
  geometry from OSRM and adds the safety score and explanation itself.
- The **Async Worker** keeps data fresh outside the request path. It gets
  event-triggered recalculation when a report reaches the verification
  threshold (NF5).
- **Geofencing runs on the phone** (`mobile/src/services/geofence.js`). The
  server never receives a continuous location stream (NF3, NF11).

## Repository layout

```
.
├── .github/workflows/ci.yml   lint, app-start smoke test, migrations on PostGIS, Docker build
├── backend/                   Python 3.11+, FastAPI
│   ├── app/
│   │   ├── main.py            composition root (create_app)
│   │   ├── config.py          all settings, from env / backend/.env
│   │   ├── api/               Backend API: one package per bounded context
│   │   │   ├── <context>/     router.py (HTTP) · service.py (domain logic) · schemas.py (Pydantic)
│   │   │   ├── dependencies.py  auth, bbox/point parsing, worker injection
│   │   │   └── routers.py     the router list main.py registers
│   │   ├── worker/            Async Worker: interface, background + Celery realisations, jobs
│   │   │   └── scoring/       segment-scoring model, SHAP, Laplace DP (not wired in yet)
│   │   ├── datalag/           persistence: SQLite stores, zone cache, ORM models, Alembic migrations
│   │   ├── external/          adapters: OSRM, Danmarks Statistik, news RSS, Wayback
│   │   └── shared/            value objects used by several subsystems (BBox, LatLon, NewsItem)
│   ├── data/                  dev SQLite files (git-ignored, created on startup)
│   ├── alembic.ini · pyproject.toml (ruff/pytest config) · requirements*.txt · .env.example
├── mobile/                    Expo app (React Navigation, no Expo Router)
│   └── src/
│       ├── index.js · App.js  entry + providers
│       ├── navigation/        bottom tabs
│       ├── features/<name>/   screens, hooks and context per feature (map, routes, walk, reports, auth, news, crimeIndex, settings)
│       ├── services/          api (REST + WS), geofence, location, geocoding
│       ├── ui/                shared presentational components
│       └── theme/
├── infrastructure/
│   ├── docker-compose.yml     postgres/postgis, osrm, backend (+ redis/worker under the "celery" profile)
│   ├── docker/backend.Dockerfile
│   └── osrm/README.md         how to build the pedestrian graph
└── docs/
    ├── architecture.md        report → code map, dependency rules, known gaps
    ├── report/                the report PDF and the course template
    ├── diagrams/              PlantUML sources of the report figures
    ├── images/                rendered figures, whiteboard wireframes
    └── drafts/                earlier Markdown drafts of report chapters (superseded by the report)
```

## Backend setup

Requires Python 3.11+.

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate            # Windows (bash: source .venv/Scripts/activate; macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
cp .env.example .env              # every key is optional, defaults are in app/config.py
uvicorn app.main:app --reload     # http://localhost:8000/docs
```

No database server is needed for development. Users, reports and the news
archive live in SQLite files under `backend/data/`, and the zone cache lives
in memory. All of them are created and filled on startup. The Async Worker
runs inside the same process (`ASYNC_WORKER=background`).

### Environment variables

See `backend/.env.example` for the full annotated list. The important ones:

| Variable | Default | Purpose |
|---|---|---|
| `JWT_SECRET_KEY` | insecure dev value | Signs session tokens. **Set it outside local dev.** |
| `OSRM_SERVER_URL` | `http://localhost:5000` | Rutemotor. `.env.example` uses the public demo instance. |
| `ASYNC_WORKER` | `background` | `background` (in-process) or `celery` (needs Redis + worker) |
| `DATABASE_URL` | local PostGIS | Target schema, used by Alembic |
| `REPORT_VERIFICATION_THRESHOLD` / `REPORT_RATE_LIMIT` | 3 / 5 per 60 min | F3 / NF10 |

### Database migrations (PostgreSQL/PostGIS target schema)

```bash
docker compose -f infrastructure/docker-compose.yml up -d postgres
cd backend
alembic upgrade head              # URL comes from DATABASE_URL
alembic upgrade head --sql        # offline: print the SQL without a database
```

The running app does not use this schema yet; see `docs/architecture.md`.

## Mobile setup

Requires Node 20+ and the Expo Go app (or an emulator).

```bash
cd mobile
npm ci
cp .env.example .env              # EXPO_PUBLIC_API_BASE_URL=http://<your LAN IP>:8000 for a real phone
npm start                         # or: npm run android | ios | web
```

`localhost` only works for the web build and simulators. On a physical phone,
point `EXPO_PUBLIC_API_BASE_URL` at your machine's LAN IP, or use
`npx expo start --tunnel`.

## Running everything with Docker

```bash
# once: build the OSRM graph, see infrastructure/osrm/README.md
docker compose -f infrastructure/docker-compose.yml up --build
```

This starts PostGIS, OSRM and the backend on `:8000`, with the in-process
worker. The Celery target architecture is opt-in:

```bash
ASYNC_WORKER=celery docker compose -f infrastructure/docker-compose.yml --profile celery up --build
```

That variant is not fully functional yet. The worker container's zone cache
and SQLite files are separate from the backend's, so zones and news computed
there do not reach the API until the Datalag moves to PostgreSQL.

## Checks

```bash
cd backend && ruff check . && pytest
cd mobile  && npm run lint && npm test
```

Tests are planned work. pytest and jest-expo are configured, but with no
tests yet `pytest` exits 5 and `npm test` reports "No tests found".

CI (`.github/workflows/ci.yml`) runs the following on every push and PR to `main`:
- Ruff
- an app-start smoke test
- `alembic upgrade head` / `downgrade base` against a PostGIS service
- ESLint
- the backend Docker build
