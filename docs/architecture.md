# Architecture: report → code

The report (`docs/report/Bachelorprojekt rapport - Google Docs.pdf`, ch. 4–5)
defines the architecture. This page says where each part lives in the code,
which dependency rules keep it that way, and where the code and the report
currently differ. Section numbers refer to the report.

## Subsystems (figur 4.2)

| Subsystem | Code | Report |
|---|---|---|
| Mobile Client | `mobile/src` | 4.3.4.2, 5.5 |
| Backend API | `backend/app/api`, composed in `backend/app/main.py` | 4.3.2, 5.2 |
| Async Worker | `backend/app/worker` | 4.3.4.5, 5.3 |
| Datalag | `backend/app/datalag` | 4.3.3, 5.4 |
| External systems | `backend/app/external` (one adapter per relation) | 4.1 |

### Backend API: bounded contexts

Each context in `app/api/<context>/` has the three roles from 5.2.1.1:

- `router.py` (boundary): HTTP in and out, status codes, nothing else.
- `service.py` (control): domain logic. It never imports FastAPI, and it is
  also called by the Async Worker.
- `schemas.py` (contract): the Pydantic models behind tabel 4.1.

| Context | Endpoints | Requirements | State |
|---|---|---|---|
| `routes` | `GET /api/routes` | F1, NF1, NF7, NF8 | OSRM + fallback; scores are stand-ins (no `segment_scores` yet) |
| `zones` | `GET /api/zones`, `GET /api/zones/status`, `WS /ws/zones` | F5, F7 | real municipality scores from Danmarks Statistik |
| `reports` | `GET/POST /api/reports`, `POST /api/reports/{id}/confirm` | F2, F3, NF4, NF5, NF10 | implemented |
| `auth` | `POST /api/auth/signup`, `/login` | F2, NF11 | implemented (PBKDF2 + HMAC-signed token) |
| `news` | `GET /api/news`, `/archive-status`, `POST /backfill` | F9 | implemented |
| `crime_index` | `GET /api/crime-index` | F4 | stub (fixed values) |
| `segments` | `GET /api/segments/{id}/explain` | NF8 | stub (fixed values) |
| `incidents` | `GET /api/incidents` | F8 | returns `[]` (no incident source yet) |

### Dependency rules

```
api/<ctx>/router ──► api/<ctx>/service ──► datalag, external, shared
                          ▲
worker/jobs ──────────────┘     (worker never imports a router)
datalag, external ──► shared, config        (never import api or worker)
```

- Only `main.py` builds subsystems. Everything else gets them injected, for
  example the Async Worker through `api/dependencies.get_async_worker`.
- The rest of the code sees the Async Worker only through the `AsyncWorker`
  interface (`worker/base.py`). Its realisation is chosen by `ASYNC_WORKER`,
  so switching to Celery changes no other subsystem (4.3.4.5).
- Protocol details (URLs, coordinate order, CSV/RSS/CDX parsing) stay inside
  `external/`. OSRM returns geometry and time only. The safety score is added
  in `api/routes/service.py` (4.3.2).
- `worker/jobs.py` calls `api/news/service` and `api/zones/crime_stats`. This
  is intentional: 5.2.1.1 places the shared services in the Backend API
  subsystem and lets the Async Worker reuse them.

### Key decisions and where they are realised

| Decision | Where |
|---|---|
| Scores precomputed outside the request path (4.2.1) | `worker/jobs.py` → `datalag` (stub for segments, real for zones) |
| Geofence evaluated on the phone, not the server (4.2.2) | `mobile/src/services/geofence.js`, `features/walk/useWalkMonitor.js` |
| Event-triggered recalculation on verification (4.2.3) | `api/reports/service.confirm_report` → `AsyncWorker.submit_recalculation` |
| DP noise once, at write time (4.2.4) | `worker/scoring/laplace.py`, to be called from `jobs.recalculate_segment_scores` |
| One background process at launch, Celery later (4.3.4.5) | `worker/background.py` (default), `worker/celery_*.py`, `tasks.py` |

## Known differences from the report

These are documented, not fixed. Each one needs a design decision or
infrastructure the dev setup does not run.

1. **The Datalag runs on SQLite plus an in-memory cache, not PostGIS**
   (tabel 5.1). The PostGIS schema exists as ORM models and Alembic
   migration `0001`, but it has drifted from what the app stores:
   - `users` lacks `email` and `password_hash`.
   - `reports` lacks `type` and `occurred_at`.
   - There is no `report_confirmations` table and no news-archive table.

   Migration `0002` is needed before the switch (5.4.3). GiST indexes on the
   geography columns are already emitted by GeoAlchemy2. You can check with
   `alembic upgrade head --sql`.
2. **No `segment_scores` pipeline yet.** Route scores are fixed stand-ins.
   `recalculate_segment_scores` only logs, and the scoring package (model,
   SHAP, Laplace) is not called by any job.
3. **The Celery realisation is incomplete.** Zone events published in the
   Celery process do not reach `/ws/zones` in the API process (this needs
   Redis pub/sub behind `api/zones/updates.py`). The zone cache and the
   SQLite stores are per-process, so docker compose runs the in-process
   worker by default.
4. **Server-initiated push (4.2.2, 4.3.2) is not implemented.** Only the
   client-local notifications exist.
5. **Tokens are HMAC-signed JSON, not a standard JWT library.** They are
   signed and expire as 4.3.2 requires, but they are not RFC 7519 compatible.
6. **The report's ch. 5 cites pre-refactor paths** (`routers/routes.py`,
   `services/auth.py`, `privacy/laplace.py`, `app/models.py`). The current
   paths are the ones in the tables above.
7. **`POST /api/news/backfill` is unauthenticated** and starts a long
   external crawl. Restrict it before any public deployment, as you should
   the `allow_origins=["*"]` CORS setting in `main.py`.
