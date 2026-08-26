# SafeRoute 🧭

AI-powered pedestrian navigation that optimizes for safety, not just speed.

SafeRoute is a full-stack navigation system that combines crime data, street lighting, foot traffic, and real-time community reports into a dynamic safety score for every street in a city. That score is fed into the routing engine as a second optimization parameter alongside travel time — so instead of only the fastest route, users get routes tailored to their personal risk tolerance, the time of day, and their surroundings.

Existing map services (Google Maps, Apple Maps) optimize almost exclusively for distance and time. For large groups of users — women walking alone at night, elderly people, tourists in unfamiliar areas, and people with anxiety or reduced mobility — perceived safety is often the deciding factor in route choice, and today's tools simply don't account for it. A 2021 UK Office for National Statistics survey found that 38% of women feel unsafe walking alone after dark. The data needed to fix this already exists (open crime data, lighting maps, foot traffic estimates) — what's missing is a system that fuses it into one actionable, dynamic signal.

## Table of Contents

- [Core Hypothesis](#core-hypothesis)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Mobile App — Pages](#mobile-app--pages)
- [Machine Learning Approach](#machine-learning-approach)
- [Privacy](#privacy)
- [Bonus: Geofenced Push Notifications](#bonus-geofenced-push-notifications)
- [Academic Relevance (Software Engineering)](#academic-relevance-software-engineering)
- [Roadmap](#roadmap)

## Core Hypothesis

Heterogeneous geospatial data sources — crime statistics, street lighting, pedestrian traffic, real-time user reports, and news — can be combined via machine learning into a per-street/per-route safety score, which can then be used as a live routing parameter alongside travel time.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Task Queue | Celery + Redis |
| Database | PostgreSQL + PostGIS |
| ML Framework | scikit-learn + SHAP (explainability) |
| Routing Engine | OSRM + Python bindings |
| Mobile Frontend | React Native + Expo |
| Map Rendering | Mapbox GL JS |
| Privacy Layer | Custom differential privacy (Laplace mechanism) |
| Containerization | Docker |
| CI/CD | GitHub Actions |

## System Architecture

- **Backend:** RESTful APIs + WebSocket-based real-time updates (live reports, moving safety zones).
- **Async processing:** Celery workers (backed by Redis) handle data ingestion, score recalculation, and news scraping/analysis without blocking API responses.
- **Data layer:** PostgreSQL with PostGIS extensions for geospatial queries (proximity search, route-to-polygon intersection, zone aggregation).
- **ML service:** scikit-learn models trained on historical crime patterns, time-of-day, day-of-week, and live event data, exposed via an internal API. SHAP is used to generate per-street explanations ("why is this street rated risky?") rather than a black-box score.
- **Routing engine:** OSRM computes candidate routes; a custom scoring layer re-ranks/annotates them using the ML-generated safety scores per road segment.
- **Privacy layer:** Laplace-noise-based differential privacy applied to aggregated user-submitted reports and location data before they influence public-facing scores, so individual users can't be re-identified from the crime/safety heatmap.

## Mobile App — Pages

### 1. Home / Map Page

The landing screen: a large interactive map (similar in spirit to ArcGIS crime dashboards) showing reported crimes as tappable pins with type, date, and details. Streets/areas are color-coded by safety:

- 🔴 Red — unsafe
- 🟡 Yellow — mixed/uncertain (~50/50)
- ⚪ No color (default) — no significant signal

Zones can be computed by the model or manually flagged (e.g. by police/admin input), and some areas shift color dynamically based on time of day. The user's live location and current route are also rendered on this map.

### 2. Route Page

Shows multiple A→B route options, sortable by time or safety level, similar to how Google Maps offers route variants — except each route carries a second metric alongside ETA:

- Route A — 30 min · Safety: Medium
- Route B — 35 min · Safety: Very Safe

Safety is expressed on a 1–10 scale so users can directly trade off speed against risk.

### 3. Latest News Page

A live, city-scoped feed of crime-related news only — filtered and kept up to date via the news-ingestion pipeline, which feeds back into the safety scoring model.

### 4. Crime Index Page

A city-level crime/safety index, similar to Numbeo's crime index, defaulting to the user's current city but searchable for any location. Includes:

- Overall Crime Index / Safety Index (0–120 scale)
- Sub-metrics: level of crime, 5-year trend, worry about burglary/mugging/car theft/assault/harassment, drug activity, property crime, violent crime, corruption
- Daytime vs. nighttime walking safety scores
- Contributor count and last-updated timestamp
- An AI-generated summary of the city's overall safety status with practical tips for visitors/residents

### 5. Settings

User preferences: default risk tolerance, notification settings, emergency contacts, unit preferences, privacy controls.

### Wireframes & UI Sketches

Early whiteboard wireframes for the core screens (see `/docs/wireframes/` for the raw photos):

#### Map Design

- Map view marks each reported incident with an X (legend: X = Crimes).
- Danger clusters are hand-outlined as a "Bad Zone" — either algorithmically detected or pre-set via API/admin input.
- Tapping an X opens a popup card with Type, Date, Info for that specific crime.
- Two routes are drawn simultaneously for comparison: a red path ("Fastest but not safe — 30 min") vs. a teal path ("Fast and safe — 34 min"), both generated by the AI based on the underlying data.

#### Route Design

- Standalone screen with From/To fields and transport-mode selector (walk / car / bike icons).
- Below that, a stacked list of route options, each showing duration + a plain-language safety label and a route-preview squiggle, e.g.:
  - 24 min — okay
  - 26 min — safe
  - 30 min — safe

#### Crime Index Design

- City header (e.g. "Delhi, India"), followed by a Crime Info block, a Diagrams etc. block, and an AI text block — the AI-generated summary/tips described in the Crime Index page above.

#### Settings

- Simple vertical list of configurable options (placeholder rows in the sketch — to be defined: risk tolerance, notification toggles, emergency contacts, units).

#### Notification Design

Two notification examples stacked on a phone mockup:

- "You have entered a red zone. Please be aware." — triggered by geofence + algorithm.
- "Time has reached [hh:mm], bad activities happen this time." — triggered by time-based conditions.

## Machine Learning Approach

- **Features:** historical crime type/frequency, time of day, day of week, street lighting presence, pedestrian density, live/community reports, news signal.
- **Explainability:** SHAP values attached to every score, so the app can tell a user why a street is rated risky (e.g. "elevated due to recent evening incidents nearby"), not just show a number.
- **Live updates:** Celery periodic tasks recompute scores as new reports, news, or time-of-day thresholds come in.
- **Community verification:** user-submitted real-time reports require nearby confirmation from other users before strongly influencing the public score, reducing spam/abuse risk.

## Privacy

All user-submitted location and report data is aggregated and perturbed using a Laplace differential privacy mechanism before being reflected in public safety scores or heatmaps. This is designed so that:

- Individual users cannot be re-identified from aggregate crime/safety visualizations.
- The system still preserves enough statistical signal for the ML model to remain useful.

## Bonus: Geofenced Push Notifications

Planned via geofencing: the app monitors the user's live location against known red/high-risk zones and time thresholds, triggering push notifications such as:

- "You have entered a high-risk zone. Please stay alert."
- "It's now past midnight — incidents are historically more frequent at this hour. Please take extra care."

An in-app emergency/panic button also allows the user to instantly share their live location with pre-selected trusted contacts.

## Academic Relevance (Software Engineering)

SafeRoute is primarily a software engineering project and fits naturally within a Software Technology specialization. It spans the full software development lifecycle:

- System architecture design — microservices, API contracts, database structure
- Backend development — RESTful APIs, asynchronous task queues, WebSocket-based real-time communication
- Machine learning engineering — feature engineering, model training/evaluation, deployment via API
- Mobile development — cross-platform app in React Native
- DevOps — containerization, CI/CD pipelines, cloud deployment
- Data engineering — ETL pipelines, geospatial data processing, PostGIS query optimization

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
