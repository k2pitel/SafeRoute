# SafeRoute 🧭

**AI-powered pedestrian navigation that optimizes for safety, not just speed.**

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![License](https://img.shields.io/badge/license-TBD-lightgrey)
![Stack](https://img.shields.io/badge/stack-React%20Native%20%7C%20Celery%20%7C%20PostGIS-blue)

SafeRoute is a full-stack navigation system that combines crime data, street lighting, foot traffic, and real-time community reports into a dynamic **safety score** for every street in a city. That score is fed into the routing engine as a second optimization parameter alongside travel time — so instead of only the fastest route, users get routes tailored to their personal risk tolerance, the time of day, and their surroundings.

Existing map services (Google Maps, Apple Maps) optimize almost exclusively for distance and time. For large groups of users — women walking alone at night, elderly people, tourists in unfamiliar areas, and people with anxiety or reduced mobility — perceived safety is often *the* deciding factor in route choice, and today's tools simply don't account for it. A 2021 UK Office for National Statistics survey found that 38% of women feel unsafe walking alone after dark. The data needed to fix this already exists (open crime data, lighting maps, foot traffic estimates) — what's missing is a system that fuses it into one actionable, dynamic signal.

---

## Table of Contents
- [Core Hypothesis](#core-hypothesis)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Repository Structure](#repository-structure)
- [Data Sources](#data-sources)
- [Database Schema (Draft)](#database-schema-draft)
- [API Overview](#api-overview)
- [Mobile App — Pages](#mobile-app--pages)
- [Wireframes & UI Sketches](#wireframes--ui-sketches)
- [Machine Learning Approach](#machine-learning-approach)
- [Privacy](#privacy)
- [Security Considerations](#security-considerations)
- [Bonus: Geofenced Push Notifications](#bonus-geofenced-push-notifications)
- [Getting Started](#getting-started)
- [Testing Strategy](#testing-strategy)
- [Academic Relevance (Software Engineering)](#academic-relevance-software-engineering)
- [Roadmap](#roadmap)
- [Team](#team)

---

## Core Hypothesis

Heterogeneous geospatial data sources — crime statistics, street lighting, pedestrian traffic, real-time user reports, and news — can be combined via machine learning into a per-street/per-route **safety score**, which can then be used as a live routing parameter alongside travel time.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Task Queue | Celery + Redis |
| Database | PostgreSQL + PostGIS |
| ML Framework | scikit-learn + SHAP (explainability) |
| Routing Engine | OSRM + Python bindings |
| Mobile Frontend | React Native + Expo |
| Map Rendering | Mapbox GL JS |
| Privacy Layer | Custom differential privacy (Laplace mechanism) |
| Containerization | Docker |
| CI/CD | GitHub Actions |

---

## System Architecture

- **Backend**: RESTful APIs + WebSocket-based real-time updates (live reports, moving safety zones).
- **Async processing**: Celery workers (backed by Redis) handle data ingestion, score recalculation, and news scraping/analysis without blocking API responses.
- **Data layer**: PostgreSQL with PostGIS extensions for geospatial queries (proximity search, route-to-polygon intersection, zone aggregation).
- **ML service**: scikit-learn models trained on historical crime patterns, time-of-day, day-of-week, and live event data, exposed via an internal API. SHAP is used to generate per-street explanations ("why is this street rated risky?") rather than a black-box score.
- **Routing engine**: OSRM computes candidate routes; a custom scoring layer re-ranks/annotates them using the ML-generated safety scores per road segment.
- **Privacy layer**: Laplace-noise-based differential privacy applied to aggregated user-submitted reports and location data before they influence public-facing scores, so individual users can't be re-identified from the crime/safety heatmap.

---

## Repository Structure

Proposed monorepo layout (subject to change as services are split out):

```
saferoute/
├── mobile/                 # React Native + Expo app
│   ├── src/
│   │   ├── screens/        # Map, Route, News, CrimeIndex, Settings
│   │   ├── components/
│   │   ├── navigation/
│   │   └── services/       # API clients, geofence logic
│   └── app.json
├── backend/
│   ├── api/                # REST + WebSocket endpoints
│   ├── workers/            # Celery tasks (score recalculation, news ingest)
│   ├── models/              # ORM models (PostgreSQL/PostGIS)
│   └── privacy/            # Laplace differential privacy layer
├── ml/
│   ├── training/            # Model training scripts
│   ├── features/            # Feature engineering pipelines
│   ├── explainability/      # SHAP integration
│   └── serving/             # Model inference API
├── routing/
│   └── osrm/                 # OSRM config, profiles, Python bindings
├── infra/
│   ├── docker/               # Dockerfiles per service
│   ├── docker-compose.yml
│   └── .github/workflows/    # CI/CD pipelines
├── docs/
│   └── wireframes/           # Whiteboard sketches, design references
└── README.md
```

---

## Data Sources

| Source | Purpose | Notes |
|---|---|---|
| Municipal open crime data portals | Historical incident type/location/date | Availability and schema vary by city; needs a per-city ingestion adapter |
| Street lighting datasets (city open data / OSM tags) | Lighting-density feature for scoring | Not available for every city — fallback to inferred estimates |
| OpenStreetMap | Base map data, road network for OSRM | |
| News APIs / RSS (local outlets) | Crime-related news feed + supplementary safety signal | Filtered via keyword/NLP classification |
| Community reports (in-app) | Real-time, crowd-verified incidents | Subject to the differential privacy layer before affecting public scores |

---

## Database Schema (Draft)

Core tables (PostgreSQL + PostGIS), simplified:

```sql
-- Reported/historical crime incidents
CREATE TABLE incidents (
    id            SERIAL PRIMARY KEY,
    type          VARCHAR(50) NOT NULL,
    description   TEXT,
    location      GEOGRAPHY(Point, 4326) NOT NULL,
    occurred_at   TIMESTAMPTZ NOT NULL,
    source        VARCHAR(50) NOT NULL,      -- 'official' | 'community' | 'news'
    verified      BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- Precomputed safety score per road segment
CREATE TABLE segment_scores (
    id            SERIAL PRIMARY KEY,
    segment_id    VARCHAR(64) NOT NULL,      -- OSRM/OSM way ID
    geom          GEOGRAPHY(LineString, 4326) NOT NULL,
    safety_score  NUMERIC(4,2) NOT NULL,      -- 1.0–10.0
    time_bucket   VARCHAR(20) NOT NULL,       -- e.g. 'day' | 'evening' | 'night'
    shap_summary  JSONB,                      -- top contributing features
    updated_at    TIMESTAMPTZ DEFAULT now()
);

-- Community-submitted real-time reports
CREATE TABLE reports (
    id            SERIAL PRIMARY KEY,
    user_id       UUID NOT NULL,
    location      GEOGRAPHY(Point, 4326) NOT NULL,
    description   TEXT,
    confirmations INTEGER DEFAULT 0,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- App users
CREATE TABLE users (
    id            UUID PRIMARY KEY,
    risk_profile  VARCHAR(20) DEFAULT 'balanced',  -- 'fast' | 'balanced' | 'safest'
    emergency_contacts JSONB,
    created_at    TIMESTAMPTZ DEFAULT now()
);
```

Spatial indexes (`GIST`) should be added on all `GEOGRAPHY` columns for query performance.

---

## API Overview

Indicative REST endpoints (finalized contracts to be defined in `backend/api/`):

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/incidents?bbox=...` | Fetch incidents within a map bounding box |
| `GET` | `/api/routes?from=&to=&mode=` | Return ranked route options with time + safety score |
| `GET` | `/api/segments/{id}/explain` | SHAP-based explanation for a segment's safety score |
| `POST` | `/api/reports` | Submit a real-time community report |
| `POST` | `/api/reports/{id}/confirm` | Confirm a nearby user's report |
| `GET` | `/api/crime-index?city=` | City-level crime/safety index + AI summary |
| `GET` | `/api/news?city=` | Latest crime-related news for a city |
| `WS` | `/ws/zones` | Live push of zone/score changes (e.g. time-of-day shifts) |

---

## Mobile App — Pages

### 1. Home / Map Page
The landing screen: a large interactive map (similar in spirit to [ArcGIS crime dashboards](https://www.arcgis.com/apps/instant/sidebar/index.html?appid=8153f961507040de8dbf9a53145f18c4)) showing reported crimes as tappable pins with type, date, and details. Streets/areas are color-coded by safety:
- 🔴 Red — unsafe
- 🟡 Yellow — mixed/uncertain (~50/50)
- ⚪ No color (default) — no significant signal

Zones can be computed by the model or manually flagged (e.g. by police/admin input), and some areas shift color dynamically based on time of day. The user's live location and current route are also rendered on this map.

### 2. Route Page
Shows multiple A→B route options, sortable by **time** or **safety level**, similar to how Google Maps offers route variants — except each route carries a second metric alongside ETA:
> *Route A — 30 min · Safety: Medium*
> *Route B — 35 min · Safety: Very Safe*

Safety is expressed on a 1–10 scale so users can directly trade off speed against risk.

### 3. Latest News Page
A live, city-scoped feed of **crime-related news only** — filtered and kept up to date via the news-ingestion pipeline, which feeds back into the safety scoring model.

### 4. Crime Index Page
A city-level crime/safety index, similar to [Numbeo's crime index](https://www.numbeo.com/crime/region_rankings_current.jsp?region=150), defaulting to the user's current city but searchable for any location. Includes:
- Overall Crime Index / Safety Index (0–120 scale)
- Sub-metrics: level of crime, 5-year trend, worry about burglary/mugging/car theft/assault/harassment, drug activity, property crime, violent crime, corruption
- Daytime vs. nighttime walking safety scores
- Contributor count and last-updated timestamp
- An **AI-generated summary** of the city's overall safety status with practical tips for visitors/residents

### 5. Settings
User preferences: default risk tolerance, notification settings, emergency contacts, unit preferences, privacy controls.

---

## Wireframes & UI Sketches

Early whiteboard wireframes for the core screens (see `/docs/wireframes/` for the raw photos):

**Map Design**
- Map view marks each reported incident with an `X` (legend: *X = Crimes*).
- Danger clusters are hand-outlined as a **"Bad Zone"** — either algorithmically detected or pre-set via API/admin input.
- Tapping an `X` opens a popup card with **Type**, **Date**, **Info** for that specific crime.
- Two routes are drawn simultaneously for comparison: a red path (*"Fastest but not safe — 30 min"*) vs. a teal path (*"Fast and safe — 34 min"*), both **generated by the AI based on the underlying data**.

**Route Design**
- Standalone screen with From/To fields and transport-mode selector (walk / car / bike icons).
- Below that, a stacked list of route options, each showing duration + a plain-language safety label and a route-preview squiggle, e.g.:
  - `24 min — okay`
  - `26 min — safe`
  - `30 min — safe`

**Crime Index Design**
- City header (e.g. *"Delhi, India"*), followed by a **Crime Info** block, a **Diagrams etc.** block, and an **AI text** block — the AI-generated summary/tips described in the Crime Index page above.

**Settings**
- Simple vertical list of configurable options (placeholder rows in the sketch — to be defined: risk tolerance, notification toggles, emergency contacts, units).

**Notification Design**
- Two notification examples stacked on a phone mockup:
  - *"You have entered a red zone. Please be aware."* — triggered by **geofence + algorithm**.
  - *"Time has reached [hh:mm], bad activities happen this time."* — triggered by **time-based conditions**.

---

## Machine Learning Approach

- **Features**: historical crime type/frequency, time of day, day of week, street lighting presence, pedestrian density, live/community reports, news signal.
- **Explainability**: SHAP values attached to every score, so the app can tell a user *why* a street is rated risky (e.g. "elevated due to recent evening incidents nearby"), not just show a number.
- **Live updates**: Celery periodic tasks recompute scores as new reports, news, or time-of-day thresholds come in.
- **Community verification**: user-submitted real-time reports require nearby confirmation from other users before strongly influencing the public score, reducing spam/abuse risk.

---

## Privacy

All user-submitted location and report data is aggregated and perturbed using a **Laplace differential privacy mechanism** before being reflected in public safety scores or heatmaps. This is designed so that:
- Individual users cannot be re-identified from aggregate crime/safety visualizations.
- The system still preserves enough statistical signal for the ML model to remain useful.

---

## Security Considerations

- **Report abuse/spam**: real-time community reports require nearby-user confirmation before meaningfully affecting public scores; rate-limiting and anomaly detection on the reports endpoint.
- **Location data handling**: live location is only transmitted while the app is in active navigation/geofence mode; historical location traces are not persisted beyond what's needed for the current session.
- **Differential privacy**: aggregated report/location data is perturbed (Laplace mechanism) before contributing to public-facing scores or heatmaps — see [Privacy](#privacy).
- **Auth**: standard JWT/OAuth2 for API access; emergency contact sharing requires explicit per-contact opt-in.
- **Data source integrity**: official crime data and news are tagged by source and confidence; community reports are weighted lower until confirmed.

---

## Bonus: Geofenced Push Notifications

Planned via **geofencing**: the app monitors the user's live location against known red/high-risk zones and time thresholds, triggering push notifications such as:
- *"You have entered a high-risk zone. Please stay alert."*
- *"It's now past midnight — incidents are historically more frequent at this hour. Please take extra care."*

An in-app **emergency/panic button** also allows the user to instantly share their live location with pre-selected trusted contacts.

---

## Getting Started

**Prerequisites**
- Python 3.11+ (backend, Celery worker, ML)
- Node.js 18+ (Expo/React Native mobile app)
- Docker & Docker Compose — only needed if you want to run Postgres/Redis/OSRM/backend in containers instead of natively

Both `backend/.env` and `mobile/.env` already exist in this repo with working local defaults (a public demo OSRM instance, `localhost` Postgres/Redis), so you generally don't need to create them yourself — copy from the corresponding `.env.example` only if you need to override something (e.g. your own Mapbox/News API keys).

### Option A — with Docker

Brings up Postgres+PostGIS, Redis, an OSRM container, and builds/runs the FastAPI backend + Celery worker images.

```bash
# from the repo root
docker compose -f infra/docker-compose.yml up -d --build

# apply DB migrations (backend/.env already points at localhost:5432,
# which is where docker-compose publishes the postgres container's port)
cd backend
pip install -r requirements.txt   # only needed to get the local `alembic` CLI
alembic upgrade head
```

The API is then live at `http://localhost:8000` (`/health` to check) and the worker container is already running Celery with beat scheduling.

Notes:
- The `osrm` service expects a prebuilt `.osrm` graph in `infra/osrm-data/` (see `routing/osrm/README.md` for how to generate one from an OSM extract). Without it, that one container will fail to start — harmless for local API/mobile work, since `backend/.env` defaults `OSRM_SERVER_URL` to a public demo OSRM server instead.
- To rebuild after changing backend code/dependencies: `docker compose -f infra/docker-compose.yml up -d --build backend worker`.
- Logs: `docker compose -f infra/docker-compose.yml logs -f backend worker`.
- Stop everything: `docker compose -f infra/docker-compose.yml down` (add `-v` to also drop the Postgres volume).

### Option B — without Docker (run everything natively)

You still need a local Postgres+PostGIS and Redis — the easiest way is to run *just* those two via Docker even in this "no Docker" flow:
```bash
docker compose -f infra/docker-compose.yml up -d postgres redis
```
or install/run them natively if you'd rather not use Docker at all.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt

# apply DB migrations
alembic upgrade head

# terminal 1 — API server
uvicorn app.main:app --reload --port 8000

# terminal 2 — Celery worker (+ beat, for scheduled score recalculation)
celery -A app.celery_app worker --beat -l info
```

Then, in another terminal, start the mobile app:
```bash
cd mobile
npm install
npx expo start          # press "w" for web, or scan the QR code in Expo Go
```

The mobile app reads `EXPO_PUBLIC_API_BASE_URL` from `mobile/.env` to find the backend. See below for how to set this depending on how you're running the app.

### Running on your phone (Expo Go)

**Normal case — same Wi-Fi, home/unrestricted network:**
1. Start the backend bound to all interfaces so devices on the network can reach it: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (from `backend/`, venv activated).
2. Find this machine's LAN IP (`ipconfig` on Windows, look for the Wi-Fi adapter's IPv4 address) and set it in `mobile/.env`: `EXPO_PUBLIC_API_BASE_URL=http://<your-lan-ip>:8000`.
3. `cd mobile && npx expo start`, then scan the printed QR code with Expo Go (Android) or the Camera app (iOS). Your phone must be on the same Wi-Fi network as this machine.

**If the app times out / Expo Go says "offline" / no data loads:**
This usually means the network won't let your phone and PC talk to each other directly — common on university/corporate Wi-Fi (client isolation) or when Windows classifies the network as "Public" (its firewall then blocks incoming connections to `node`/`python` unless an exception was already granted, even though both devices are on the same Wi-Fi name). If you can't fix the network/firewall (e.g. it's locked down by IT policy), tunnel both services instead so traffic goes over the internet rather than the local network:

1. Backend tunnel: `cloudflared tunnel --url http://localhost:8000` (no account needed; install via `winget install cloudflared` if it's missing). Copy the `https://*.trycloudflare.com` URL it prints.
2. Set that URL in `mobile/.env`: `EXPO_PUBLIC_API_BASE_URL=https://<your-subdomain>.trycloudflare.com`.
3. Start Expo in tunnel mode instead of the default: `npx expo start --tunnel` (from `mobile/`). This also routes the JS bundle over the internet, avoiding the same firewall issue for Metro.
4. Scan the QR code / open the `exp://` link Expo prints in Expo Go.

Note: `EXPO_PUBLIC_*` env vars are baked into the JS bundle at Metro start time — if you change `mobile/.env`, fully restart `npx expo start` (a hot reload isn't enough) for the new value to take effect.

**Environment variables reference** (see `backend/.env.example` and `mobile/.env.example`):
```
# backend/.env
DATABASE_URL=postgresql://saferoute:saferoute@localhost:5432/saferoute
REDIS_URL=redis://localhost:6379/0
MAPBOX_ACCESS_TOKEN=...
OSRM_SERVER_URL=https://routing.openstreetmap.de/routed-foot   # or http://localhost:5000 if running OSRM locally
NEWS_API_KEY=...
DP_EPSILON=1.0

# mobile/.env
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN=...
```

---

## Testing Strategy

| Layer | Approach |
|---|---|
| Backend API | Unit tests (pytest) per endpoint; contract tests against the OpenAPI spec |
| ML models | Offline evaluation on held-out historical data (precision/recall on high-risk segment classification); SHAP output sanity checks |
| Routing | Integration tests comparing OSRM baseline routes vs. safety-adjusted routes for known test cities |
| Mobile app | Component tests (Jest + React Native Testing Library); manual QA on wireframed flows above |
| CI/CD | GitHub Actions run lint + tests on every PR; Docker image build verified before merge to `main` |

---

## Academic Relevance (Software Engineering)

SafeRoute is primarily a software engineering project and fits naturally within a **Software Technology** specialization. It spans the full software development lifecycle:

- **System architecture design** — microservices, API contracts, database structure
- **Backend development** — RESTful APIs, asynchronous task queues, WebSocket-based real-time communication
- **Machine learning engineering** — feature engineering, model training/evaluation, deployment via API
- **Mobile development** — cross-platform app in React Native
- **DevOps** — containerization, CI/CD pipelines, cloud deployment
- **Data engineering** — ETL pipelines, geospatial data processing, PostGIS query optimization

---

## Roadmap

- [ ] Define API contracts (routing, scoring, reports, news)
- [ ] Set up PostgreSQL + PostGIS schema for crime/lighting/traffic data
- [ ] Stand up OSRM instance + Python bindings
- [ ] Baseline scikit-learn safety-scoring model + SHAP explanations
- [ ] Celery + Redis async pipeline for score recalculation
- [ ] React Native + Expo app shell (5 pages)
- [ ] Mapbox GL JS map + zone color overlays
- [ ] Differential privacy layer for aggregated reports
- [ ] Geofencing + push notification service
- [ ] Docker Compose for local dev, GitHub Actions CI/CD

---

## Team

| Name | Role |
|---|---|
| TBD | Backend / Data Engineering |
| TBD | Machine Learning |
| TBD | Mobile Development |
| TBD | DevOps / CI/CD |

---

## License
TBD

## Contributing
TBD — contribution guidelines will be added as the project structure stabilizes.
