# 5. Design og implementering

## 5.1 Introduktion

Dette kapitel beskriver design og implementering af de fire delsystemer fra arkitekturen i kapitel 4 (figur 4.2): **Backend API**, **Async Worker**, **Datalag** og **Mobile Client**. Kapitlet følger en top-down-tilgang: hvert delsystem præsenteres først som en helhed (struktur og intern interaktion), hvorefter de centrale komponenter åbnes op enkeltvis. Hvert delsystem beskrives udelukkende ud fra sine egne komponenter; de øvrige delsystemer kendes kun gennem grænsefladerne fra afsnit 4.3.2.

Kapitel 4 beskrev den *planlagte* arkitektur. Den nuværende implementering realiserer den samme opdeling og de samme grænseflader, men bruger bevidst forenklede udgaver af to delsystemer, så hele systemet kan køres på én udviklermaskine uden Docker. Tabel 5.1 opsummerer forskellen og danner rammen for resten af kapitlet.

**Tabel 5.1: Planlagt vs. nuværende realisering af delsystemerne**

| Delsystem | Planlagt (kapitel 4) | Nuværende implementering | Konsekvens |
|---|---|---|---|
| Backend API | FastAPI, REST + WebSocket | FastAPI, 8 routere + `/ws/zones` | Som planlagt; tre endpoints er stadig stubs (afsnit 5.2) |
| Async Worker | Enkelt baggrundsproces → Celery/Redis ved vækst | To `asyncio`-løkker startet i FastAPI's `lifespan` (samme proces) | Svarer til lanceringsvarianten fra afsnit 4.3.4.5; Celery-opgaverne findes som stubs |
| Datalag | PostgreSQL + PostGIS | To SQLite-filer + en in-memory cache; PostGIS-skemaet findes som ORM-modeller og Alembic-migration | Ingen geospatiale indeks; ingen `segment_scores` endnu (afsnit 5.4) |
| Mobile Client | React Native + Expo | React Native + Expo, 4 faner | Geofence-modulet er implementeret men endnu ikke koblet på (afsnit 5.5) |

Rutemotoren (OSRM) er i udviklingsmiljøet ikke selvhostet som planlagt i figur 4.3; `OSRM_SERVER_URL` peger på den offentlige instans `routing.openstreetmap.de/routed-foot`. Grænsefladen er den samme, så skiftet til en selvhostet container kræver kun en ændring af miljøvariablen.

## 5.2 Delsystem Backend API

### 5.2.1 Introduktion

Backend API har ansvaret for at besvare alle forespørgsler fra Mobile Client: ruteforslag med tryghedsscore (F1), zone-polygoner (F7), indrapportering og verificering af hændelser (F2, F3), nyhedsfeed (F9), bytryghedsoversigt (F4) samt login. Delsystemet er skrevet i Python 3 med FastAPI og afvikles af Uvicorn.

#### 5.2.1.1 Struktur af delsystem

Backend API er opdelt i tre lag, som vist i komponentdiagrammet i figur 5.1:

- **Routers** (boundary): én FastAPI-`APIRouter` pr. ressource (`auth`, `reports`, `routes`, `zones`, `news`, `crime_index`, `incidents`, `segments`). En router oversætter HTTP til funktionskald og validerer ind- og uddata, men indeholder så lidt forretningslogik som muligt.
- **Services** (control): genbrugelig logik, som flere routere eller Async Worker deler: `auth` (adgangskoder og tokens), `crime_stats` (kommunal kriminalitetsscore og cache) og `danish_places` (stednavne-opslag til nyheder).
- **Schemas**: Pydantic-modeller (`RouteOption`, `ReportCreate`, `ReportOut`, `ZoneOut`, `NewsItem` m.fl.), der definerer kontrakten i tabel 4.1. FastAPI validerer automatisk alle requests mod dem og returnerer `422` ved fejl, og de bruges samtidig til at generere OpenAPI-dokumentationen.

Datalaget tilgås kun gennem modulerne `local_store` og `news_archive` (afsnit 5.4), så routerne ikke kender til SQL eller filplaceringer. `main.py` samler routerne, slår CORS til og starter Async Worker's løkker i applikationens `lifespan`.

*Figur 5.1: Backend API, komponentdiagram (se `backend-komponenter.puml`).*

Opdelingen i routers og services er valgt, fordi den samme logik skal kunne kaldes fra flere steder: `auth.get_current_user_id` bruges som FastAPI-dependency af både `POST /api/reports` og `POST /api/reports/{id}/confirm`, og `news.poll_and_archive_once` kaldes både af Async Worker og indirekte af `GET /api/news`. Det giver høj samhørighed i hvert modul og lav kobling mellem routerne indbyrdes; ingen router importerer en anden router.

#### 5.2.1.2 Interaktion mellem komponenter

Figur 5.2 viser det interne forløb for UC2 (Indrapportér hændelse). Autentificeringen er placeret som en FastAPI-dependency (`Depends(get_current_user_id)`) og ikke inde i routerfunktionen. Dermed afvises en request uden gyldigt token med `401`, før routerens egen kode overhovedet køres, og kravet om login (F2, UC2 udvidelse 3a) kan ikke glemmes i et nyt endpoint, så længe dependency'en er erklæret i signaturen. `ReportOut` indeholder bevidst ikke `user_id`, så hvem der har indsendt en rapport aldrig sendes videre til andre brugere.

*Figur 5.2: Sekvensdiagram, UC2 internt i Backend API (se `seq-backend-uc2.puml`).*

### 5.2.2 Design og implementering af rutetjenesten (`routers/routes.py`)

Rutetjenesten realiserer Backend API's del af UC1. Logikken er vist som aktivitetsdiagram i figur 5.3, da den er et lineært dataflow med to fejlgrene frem for et objektsamspil.

*Figur 5.3: Aktivitetsdiagram for `GET /api/routes` (se `akt-backend-ruter.puml`).*

Endpointet modtager `from` og `to` som `"lat,lon"` og kalder OSRM's Route-service med `alternatives=true`, så OSRM leverer op til tre alternative gangruter. Bemærk, at OSRM forventer koordinaterne i rækkefølgen `lon,lat`; byttet sker ét sted, i URL-opbygningen. Kaldet er asynkront (`httpx.AsyncClient`, timeout 10 s), så en langsom OSRM ikke blokerer andre forespørgsler i samme proces, hvilket understøtter gennemløbskravet i NF1.

Robusthedskravet NF7 er implementeret ved, at enhver HTTP-fejl, timeout, ugyldig JSON eller et tomt `routes`-svar fører til `_fallback_routes()`, som returnerer to lige-linje-forslag i stedet for en fejl. Brugeren får dermed altid et svar, også når rutemotoren er nede.

**Tryghedsscoren er p.t. en stand-in.** Den planlagte løsning fra afsnit 4.2.1 er at slå forudberegnede scorer op i `segment_scores` for de vejsegmenter, ruten passerer. Den tabel er endnu ikke befolket (afsnit 5.4), så forslagene sorteres i stedet efter varighed, og det hurtigste tildeles 4,2, det næste 8,6 og resten 6,5. Det er en bevidst pladsholder, der bevarer UI'ets "hurtig vs. tryg"-afvejning og den fulde kontrakt (`RouteOption`), så Mobile Client ikke skal ændres, når den rigtige scoring kobles på. Scoren oversættes til en tekstlabel med faste grænser: under 4 "not safe", under 6 "okay", under 8 "safe", ellers "very safe".

### 5.2.3 Design og implementering af autentificering (`services/auth.py`)

Kapitel 4 krævede signerede, tidsbegrænsede tokens i en `Authorization: Bearer`-header. Det er implementeret uden eksterne biblioteker, med Pythons standardbibliotek:

- **Adgangskoder** hashes med PBKDF2-HMAC-SHA256, 200.000 iterationer og et tilfældigt 16-byte salt pr. bruger, gemt som `salt$digest`. Sammenligningen bruger `hmac.compare_digest`, som tager konstant tid og derfor ikke lækker information via timing.
- **Tokens** består af en base64url-kodet JSON-payload `{"sub": user_id, "exp": ...}` og en HMAC-SHA256-signatur over payloaden med `JWT_SECRET_KEY`. Formatet ligner en JWT, men er ikke en standard-JWT (der er ingen header-del). Levetiden er 30 dage, fordi der ikke er noget refresh-flow.
- `get_current_user_id` afviser manglende header, forkert skema, ugyldig signatur og udløbet token med `401`.

Valget af standardbiblioteket frem for f.eks. `bcrypt` og `PyJWT` følger samme princip som resten af udviklingsopsætningen: færrest mulige afhængigheder. Det er et kendt kompromis: skal tokens kunne valideres af andre tjenester, bør formatet skiftes til en rigtig JWT, og `JWT_SECRET_KEY` skal sættes i miljøet, da standardværdien kun er beregnet til udvikling.

Mobile Client gemmer token og bruger i `expo-secure-store` (afsnit 5.5), så login overlever en genstart af appen.

### 5.2.4 Design og implementering af zoner (`routers/zones.py` + `services/crime_stats.py`)

Zonerne til F7 og geofencing (F5) er det eneste sted i systemet, hvor rigtige kriminalitetsdata allerede driver en score. Officielle danske data findes ikke med koordinater pr. hændelse, kun som optællinger pr. kommune, så en zone er en kommunepolygon.

Scoren beregnes i tre trin:

1. Antal voldsforbrydelser (Danmarks Statistik, tabel STRAF11, kode 12) summeres over de seneste fire kvartaler, så små kommuner ikke domineres af kvartalsvis støj.
2. Raten pr. 100.000 indbyggere beregnes med befolkningstallet fra FOLK1A.
3. Raten omregnes til en score med en z-score i forhold til landsgennemsnittet:

```
z     = (rate − gennemsnit) / standardafvigelse
score = clamp(5,5 − 1,5 · z ; 1 ; 10)
```

En z-score er valgt frem for percentilrangering, fordi percentiler altid ville farve en fast andel af landet "utryg", uanset hvor lille den reelle spredning er. Med z-scoren lander en gennemsnitlig kommune på 5,5, og kun statistisk afvigende kommuner bliver markeret. Labelgrænserne er 3,6 ("unsafe", ca. +1,25 standardafvigelser) og 4,4 ("mixed", ca. +0,75 standardafvigelser); resten er "safe".

`GET /api/zones?bbox=` filtrerer de cachede polygoner med en simpel bounding-box-overlapstest. Kommuner med øer kommer tilbage som flere polygoner med samme navn, så hvert ekstra stykke får et suffiks (`samsø-2`), da Mobile Client bruger id'et som React-nøgle. Er cachen tom, fordi kilden var utilgængelig, returneres en tom liste frem for pladsholderdata.

`/ws/zones` er stadig en stub, der sender syntetiske opdateringer hvert 5. sekund; den rigtige udgave skal publicere ændringer fra Async Worker.

### 5.2.5 Design og implementering af differential privacy (`privacy/laplace.py`)

Laplace-mekanismen til NF11 er implementeret: `add_dp_noise(value, sensitivity, epsilon)` lægger støj fra Laplace(0, sensitivity/ε) på en aggregeret værdi og klipper til ≥ 0, da en optælling ikke må blive negativ. `privatize_grid_counts` anvender den på en hel tabel af celleoptællinger, og ε læses fra `settings.dp_epsilon` (1,0, jf. afsnit 4.2.4). Modulet kaldes endnu ikke af nogen endpoint. Det skal kaldes fra Async Worker's scoringspipeline, på det tidspunkt hvor aggregatet skrives, jf. arkitekturbeslutningen i afsnit 4.2.4, og ikke ved hver læsning (averaging-angreb).

### 5.2.6 Øvrige endpoints

`GET /api/crime-index` (F4) og `GET /api/segments/{id}/explain` (NF8) returnerer faste, repræsentative værdier, så Mobile Client's skærme kan udvikles mod den endelige kontrakt. `GET /api/incidents` returnerer en tom liste, indtil der findes en rigtig hændelseskilde. Det er valgt frem for at vise opdigtede hændelser på kortet.

### 5.2.7 Tests og resultater

Backend API testes med `pytest` og FastAPI's `TestClient` (mappen `backend/tests/`). Alle tests isoleres fra udviklingsmiljøet: begge SQLite-stores omdirigeres til midlertidige filer pr. test, `lifespan` køres ikke (så baggrundsløkkerne ikke rammer netværket), og OSRM erstattes af en `httpx.MockTransport`.

**Tabel 5.2: Udvalgte enhedstests i Backend API**

| Komponent | Test | Forventet resultat | Status |
|---|---|---|---|
| services.auth | Adgangskode hash → verify | Rigtig accepteres, forkert afvises | ✓ |
| services.auth | Samme adgangskode hashes to gange | Forskellige hashes (unikt salt) | ✓ |
| services.auth | Token med ændret signatur | Afvises | ✓ |
| services.auth | Udløbet token | Afvises | ✓ |
| services.auth | Manglende/forkert `Authorization`-header | `401` | ✓ |
| routes | Labelgrænser 1 / 3,99 / 4 / 6 / 8 / 10 | Korrekt label pr. grænse | ✓ |
| crime_stats | Gennemsnitlig kommune | Score 5,5 | ✓ |
| crime_stats | Ekstrem outlier | Score klippes til [1; 10] | ✓ |
| zones | Labelgrænser 3,5 / 3,6 / 4,3 / 4,4 | unsafe / mixed / mixed / safe | ✓ |
| privacy.laplace | ε = 0 | `ValueError` | ✓ |
| privacy.laplace | 200.000 stikprøver, b = 1 | Middel ≈ 0, varians ≈ 2b² = 2 (±3%) | ✓ |
| privacy.laplace | Støj på optælling 0 (1.000 gange) | Aldrig negativ | ✓ |

**Tabel 5.3: Interne integrationstests i Backend API**

| Interface | Test | Status |
|---|---|---|
| auth-router → services.auth → local_store | Signup returnerer `201` + token; samme email igen giver `409`; email normaliseres til små bogstaver | ✓ |
| auth-router → local_store | Login med forkert adgangskode `401`, rigtig `200` | ✓ |
| reports-router → services.auth | Rapport uden token `401` | ✓ |
| reports-router → local_store | Ny rapport `201` med `confirmations = 0` og synlig i `GET /api/reports` for bbox'en (NF4) | ✓ |
| reports-router → local_store | Rapport uden for bbox returneres ikke | ✓ |
| reports-router → schemas | `user_id` indgår hverken i oprettelses- eller listesvar | ✓ |
| reports-router → local_store | Bekræftelse øger `confirmations` med 1; ukendt id giver `404`; uden token `401` | ✓ |
| routes-router → OSRM (mock) | URL indeholder `lon,lat`-rækkefølge og `alternatives=true`; svar sorteres hurtigst først | ✓ |
| routes-router → OSRM (mock) | OSRM utilgængelig eller tomt svar → fallback, `200` med 2 forslag (NF7) | ✓ |
| zones-router → crime_stats | Bbox-filtrering og unikke id'er for ø-stykker; tom cache → tom liste | ✓ |

**Testmetrikker.** Testsuiten indeholder 45 automatiserede tests for backend'en (inkl. Async Worker og Datalag, afsnit 5.3–5.4): 44 bestod, og 1 er markeret som forventet fejl, fordi den dokumenterer en fundet defekt (afsnit 5.3.4). Line coverage målt med `pytest-cov` for de centrale komponenter:

| Modul | Line coverage |
|---|---|
| `routers/auth.py`, `routers/reports.py`, `routers/routes.py` | 100% |
| `services/local_store.py`, `privacy/laplace.py` | 100% |
| `services/auth.py` | 96% |
| `services/news_archive.py` | 95% |
| `routers/zones.py` | 83% (WebSocket-stubben er ikke testet) |
| Hele `app/` | 60% |

Den samlede dækning trækkes ned af moduler, der ikke er en del af den kørende løsning (`models.py`, `database.py`, `tasks.py`, `celery_app.py`: 0%) og af netværkskode, der kun kører mod eksterne kilder (`crime_stats.py` 40%, `news.py` 31%, `news_backfill.py` 0%).

### 5.2.8 Delkonklusion

Backend API er implementeret som en lagdelt FastAPI-applikation, hvor routere håndterer HTTP, services indeholder den delte logik, og Pydantic-schemas fastholder kontrakten fra tabel 4.1. Login, indrapportering, verificering, ruteforslag med OSRM-fallback og zoner baseret på rigtige data fra Danmarks Statistik virker og er dækket af enheds- og integrationstests. De væsentligste mangler i forhold til kravene er, at tryghedsscoren for ruter stadig er en pladsholder (F1, NF8), at samme bruger kan bekræfte en rapport flere gange, inklusive sin egen, og at der ikke er rate limiting på indrapportering (F3, NF10).

## 5.3 Delsystem Async Worker

### 5.3.1 Introduktion

Async Worker har ansvaret for de periodiske opgaver, der holder data friske uden at belaste forespørgselsvejen: indsamling af kriminalitetsnyheder og genberegning af zonescorer. I overensstemmelse med lanceringsvarianten i afsnit 4.3.4.5 er den realiseret som en enkelt, tidsstyret baggrundsproces, nærmere bestemt to `asyncio`-tasks, som startes i FastAPI's `lifespan` og stoppes, når applikationen lukker.

### 5.3.2 Struktur og interaktion

Figur 5.4 viser de to løkker som et aktivitetsdiagram, da Async Worker er et rent dataflow uden tilstand mellem kørslerne udover hvad der skrives til Datalaget.

*Figur 5.4: Aktivitetsdiagram, Async Worker's to løkker (se `akt-worker-nyheder.puml`).*

- **Nyhedspolleren** kører hvert 15. minut: henter 11 danske RSS-feeds (DR, Ekstra Bladet, Politiken, Berlingske og syv TV2-regionalstationer) parallelt med `asyncio.gather(..., return_exceptions=True)`, filtrerer på krimi-nøgleord eller -kategorier, placerer hver nyhed geografisk og arkiverer den.
- **Statistikløkken** kører hver 6. time og genopbygger zone-cachen i `crime_stats` (afsnit 5.2.4). Kildedataene opdateres kun kvartalsvis, så intervallet er rigeligt.

Begge løkker fanger alle undtagelser, logger dem og prøver igen ved næste interval, så en fejlende ekstern kilde aldrig stopper backend'en (NF7). Parallelhentningen med `return_exceptions=True` betyder desuden, at ét utilgængeligt feed kun fjerner sine egne nyheder fra kørslen.

### 5.3.3 Design og implementering af nyhedsindsamlingen

RSS-feeds rummer kun de seneste 1-2 dages nyheder. For at opbygge historik gemmer polleren hver ny nyhed i `news_archive` (afsnit 5.4), hvor URL'en er primærnøgle, så de samme nyheder, der serveres ved hver polling, ikke dubleres. Historiske nyheder fra 2020 og frem kan desuden importeres én gang via `POST /api/news/backfill`, som læser URL-indekset fra Internet Archive's Wayback Machine og udleder en overskrift af URL'ens slug, uden at hente artiklernes indhold.

Nyhederne indeholder ingen koordinater. `danish_places.find_location` søger derfor titel og beskrivelse igennem efter ét af 135 danske by-, bydels- og kommunenavne (ordgrænse-regex, kompileret én gang). Findes intet sted, henter polleren artiklens `<p>`-afsnit og prøver igen. Kun `<p>`-indhold bruges, fordi menuer, footere og "relaterede artikler" ofte nævner andre byer og ellers giver forkerte placeringer. Berigelsen sker kun i baggrundsløkken, aldrig i det interaktive `GET /api/news`, så brugeren ikke venter på den.

Celery-opgaverne `recalculate_segment_scores` og `ingest_news` (`tasks.py`, med Beat-skema hvert 15./30. minut) er bevaret som stubs og beskriver målarkitekturen: hent hændelser, byg features (`ml/features.py`), kør modellen med SHAP (`ml/serving.py`), læg DP-støj på og skriv til `segment_scores`. Modellen (`GradientBoostingRegressor`) kan trænes end-to-end med `ml/train.py`, men kun på syntetiske data.

### 5.3.4 Tests og resultater

| Test | Forventet resultat | Status |
|---|---|---|
| Krimi-filter: nøgleord i titel | Medtages | ✓ |
| Krimi-filter: kategori "Krimi" uden nøgleord | Medtages | ✓ |
| Krimi-filter: ikke-krimi titel og kategori | Frasorteres | ✓ |
| `find_location` med bynavn / uden stednavn | Byens koordinat / `(None, None)` | ✓ |
| Bydel vinder over by ("Nørrebro i København") | Nørrebros koordinat | ✗ (forventet fejl) |
| Arkivering af samme nyhed to gange | 1 ny, derefter 0 | ✓ |
| Årsfilter i arkivet | Kun nyheder fra det valgte år | ✓ |

Testen af bydel-før-by afslørede en defekt: stednavnene sorteres efter længde (længst først), ud fra den antagelse at en bydel altid har et længere navn end sin by. "københavn" (9 tegn) er dog længere end "nørrebro" (8 tegn), så en nyhed, der nævner begge, placeres i Københavns centrum. Testen er bevaret som forventet fejl (`xfail`), indtil sorteringen ændres til at prioritere bydele eksplicit.

Statistikløkkens netværkskald og selve løkkerne er ikke automatisk testet; at de kører, er verificeret i backend-loggen fra udviklingsmiljøet.

### 5.3.5 Delkonklusion

Async Worker er realiseret som to robuste `asyncio`-løkker i Backend API's proces, hvilket er tilstrækkeligt ved den belastning, NF1 lægger op til, og ikke kræver Redis eller en separat worker-container. Nyhedsindsamlingen og zone-statistikken kører i drift; den egentlige scoringspipeline med model, SHAP og differential privacy (og dermed NF5 og NF8) er designet og forberedt i `tasks.py` og `ml/`, men endnu ikke implementeret.

## 5.4 Delsystem Datalag

### 5.4.1 Introduktion

Datalaget har ansvaret for at persistere brugere, indrapporteringer, nyhedsarkivet og, i målarkitekturen, hændelser og forudberegnede segmentscorer. Figur 5.5 viser både den nuværende realisering og målskemaet.

*Figur 5.5: Databaseskema, nuværende SQLite-realisering og PostGIS-målskema (se `datalag-er.puml`).*

### 5.4.2 Design og implementering af nuværende realisering (SQLite)

Datalaget er p.t. realiseret som to SQLite-filer og en in-memory cache:

- **`local_store.db`**: `users` (UUID som tekst-PK, unik `email`, `password_hash`) og `reports` (auto-increment-PK, `type`, `latitude`/`longitude` som `REAL`, `occurred_at`, `confirmations` med standardværdi 0). `user_id` er en logisk reference uden fremmednøgle-constraint.
- **`news_archive.db`**: `news_items` med `url` som primærnøgle. PK'en er selve dubletkontrollen: `INSERT` af en kendt URL fejler med `IntegrityError`, som fanges og tælles som "ikke ny".
- **In-memory cache** i `crime_stats` for kommunepolygoner og scorer, da de kan genberegnes fra kilden og kun ændres kvartalsvis.

Tabellerne oprettes idempotent med `CREATE TABLE IF NOT EXISTS` ved opstart. Hver operation åbner og lukker sin egen forbindelse via en context manager, der committer ved succes, så der ikke deles forbindelser mellem tråde. Tidsstempler gemmes som ISO 8601-tekst, som sorterer korrekt alfabetisk; det udnyttes af årsfilteret i arkivet (`published_at >= 'ÅÅÅÅ-01-01' AND < 'ÅÅÅÅ+1-01-01'`) uden at hver række skal parses.

Bbox-forespørgslen på rapporter er et `BETWEEN` på `longitude` og `latitude` uden indeks, altså en fuld tabelscanning. Det er acceptabelt ved prototypens datamængde, men er netop den forespørgsel, der skal flyttes til et GIST-indeks i målskemaet.

SQLite er valgt i udviklingsfasen, fordi det ikke kræver en databaseserver. Afsnit 4.3.4.3 fravalgte SQLite til drift, fordi den kun tillader én skriver ad gangen; det gælder fortsat.

### 5.4.3 Design af målskema (PostgreSQL + PostGIS)

Målskemaet findes som SQLAlchemy/GeoAlchemy2-modeller (`app/models.py`) og som Alembic-migrationen `0001_initial_schema`, der opretter PostGIS-udvidelsen og tabellerne `users`, `incidents`, `segment_scores` og `reports`. Positioner er `GEOGRAPHY(POINT, 4326)` og vejsegmenter `GEOGRAPHY(LINESTRING, 4326)`, så afstande beregnes i meter på jordkuglen. `segment_scores` har et B-tree-indeks på `segment_id`, og `shap_summary` er `JSONB` til forklaringen bag scoren (NF8). `reports.user_id` er en rigtig fremmednøgle til `users`.

Før skiftet fra SQLite kræves en migration `0002`, fordi de to skemaer er gledet fra hinanden under udviklingen:

- `users` mangler `email` og `password_hash` (login blev tilføjet efter migrationen).
- `reports` mangler `type` og `occurred_at`.
- GIST-indeks på `location` og `geom` bør erklæres eksplicit i migrationen, så bbox- og rute-mod-segment-opslagene kan køre som indekserede forespørgsler (`ST_Intersects`, `ST_DWithin`), jf. målet på under 10 ms i afsnit 4.2.1.

### 5.4.4 Tests og resultater

Datalaget testes gennem integrationstestene i tabel 5.3 og arkivtestene i afsnit 5.3.4, mod midlertidige SQLite-filer. `local_store.py` har 100% og `news_archive.py` 95% line coverage. Målskemaet er ikke testet, da det ikke køres i udviklingsmiljøet; CI-workflowet starter dog en `postgis/postgis:16-3.4`-service, så migrationen kan testes dér.

### 5.4.5 Delkonklusion

Datalaget dækker i dag alle de data, den kørende løsning har brug for, med et minimum af infrastruktur. Målskemaet i PostGIS er designet og versioneret i Alembic, men skal opdateres med en migration, før det kan erstatte SQLite, og geospatiale indeks skal tilføjes for at indfri performanceforudsætningerne fra kapitel 4.

## 5.5 Delsystem Mobile Client

### 5.5.1 Introduktion

Mobile Client er den del af systemet, brugeren interagerer med. Den har ansvaret for kortvisning, rutesøgning og -valg (UC1), indrapportering (UC2), nyhedsfeed, bytryghedsoversigt og indstillinger, samt den lokale geofence-evaluering, som arkitekturen bevidst placerede på telefonen (afsnit 4.2.2). Den er skrevet i JavaScript med React Native og Expo og kører på iOS og Android fra samme kodebase (NF12), samt i en begrænset web-udgave.

#### 5.5.1.1 Struktur af delsystem

Figur 5.6 viser komponentstrukturen. `App` pakker hele appen ind i to React-contexts og en tab-navigator med fire faner (Map, News, Crime Index, Settings):

- **Contexts** (delt tilstand): `AuthProvider` holder den indloggede bruger og eksponerer `login`, `signup` og `logout`. `ActiveRouteProvider` holder den valgte rute. En context er valgt frem for at sende data via props, fordi rutevalget sker i `RoutePanel`, mens tegningen sker i `MapScreen`, og fordi der findes to varianter af kortskærmen (se nedenfor).
- **Screens**: én pr. fane. `MapScreen.js` bruger `react-native-maps`; `MapScreen.web.js` vælges automatisk af Metro på web, hvor `react-native-maps` ikke findes, og viser i stedet en liste.
- **Components**: `RoutePanel` (fra/til-søgning og ruteliste, foldet sammen over kortet), `PlaceSearchInput`, `ReportModal` og `AuthPromptModal`.
- **Services** (boundary mod omverdenen): `api` (Backend API), `geocoding` (Nominatim) og `geofence` (telefonens lokation og notifikationer).

*Figur 5.6: Mobile Client, komponentdiagram (se `mobile-komponenter.puml`).*

Ingen skærm eller komponent kalder `fetch` direkte; alle kald til Backend API går gennem `services/api.js`. Det samler tre ansvar ét sted: basis-URL'en (`EXPO_PUBLIC_API_BASE_URL`), automatisk `Authorization: Bearer`-header (sat af `AuthProvider` via `setAuthToken`, så kaldstederne ikke kender til tokenet) og fejlhåndtering, hvor FastAPI's `detail`-felt omsættes til en læsbar besked. Ved valideringsfejl (`422`) er `detail` en liste, som samles til én tekst.

#### 5.5.1.2 Interaktion mellem komponenter

Figur 5.7 viser UC1 internt i klienten. Stedsøgningen i `PlaceSearchInput` venter 400 ms efter sidste tastetryk og kræver mindst to tegn, før `geocoding.searchPlaces` kaldes. Det holder klienten under Nominatims grænse på ca. én forespørgsel i sekundet. Resultaterne vægtes mod brugerens position (blødt `viewbox` på ±0,2°) og dedupliceres på gade + by. Når en rute vælges, skrives den til `ActiveRouteContext`, og `MapScreen` reagerer ved at tegne GeoJSON-geometrien som en polyline (grøn ved score ≥ 6,5, ellers rød) og zoome kameraet ind på den.

*Figur 5.7: Sekvensdiagram, UC1 internt i Mobile Client (se `seq-mobile-uc1.puml`).*

Figur 5.8 viser UC2. Positionen hentes, før login kontrolleres, så rapportens koordinat er brugerens aktuelle position (UC2 trin 2). Er brugeren ikke logget ind, åbnes `AuthPromptModal` først, og rapportformularen åbnes kun via `onAuthenticated`. Afbryder brugeren login, oprettes der ingen rapport (udvidelse 3a). Login er derimod ikke krævet for at søge en rute (NF9).

*Figur 5.8: Sekvensdiagram, UC2 internt i Mobile Client (se `seq-mobile-uc2.puml`).*

### 5.5.2 Design og implementering af kortskærmen (`MapScreen`)

`MapScreen` viser tre slags markører: hændelser (rød, fra `/api/incidents`, p.t. tom), community-rapporter (orange, fra `/api/reports`) og kriminalitetsnyheder (blå). Rapporter og hændelser hentes igen, når kortets centrum flytter sig, for den synlige bbox. Nyheder er landsdækkende og hentes derfor kun én gang, for alle arkiverede år.

Nyheder placeres i et bycentrum (afsnit 5.3.3), så mange historier om samme by ville ligge på præcis samme punkt, og kun den øverste kunne trykkes på. `jitterCoordinate` spreder derfor hver markør deterministisk 450 m–1,1 km ud fra centret, med en hash af URL'en som frø, så den samme nyhed altid lander samme sted. Et tryk på en markør viser et informationskort med type, tidspunkt og beskrivelse (F8).

Farvekodede zoner (F7) vises ikke i den nuværende version; `api.getZones` er implementeret, men kaldes ikke fra kortskærmen.

### 5.5.3 Design og implementering af geofencing (`services/geofence.js`)

Geofence-modulet realiserer den klientlokale løsning fra afsnit 4.2.2 (figur 4.5). `startGeofenceWatch(redZones)` starter `Location.watchPositionAsync` med `timeInterval: 15000` og `distanceInterval: 25`, svarende direkte til NF3, og evaluerer to uafhængige conditions for hver ny position. Logikken er vist som tilstandsmaskine i figur 5.9.

*Figur 5.9: Tilstandsdiagram for geofence-evalueringen (se `state-geofence.puml`).*

- **Zone-condition**: et point-in-polygon-tjek (ray casting, uden eksterne biblioteker) mod hver rødzone. Der notificeres kun ved *overgangen* fra udenfor til indenfor (`lastZoneState`), så brugeren ikke får en ny notifikation hvert 15. sekund, mens vedkommende er i zonen.
- **Tids-condition**: mellem kl. 00 og 05 notificeres der én gang pr. ny time (`lastHourAlerted`).

Notifikationen planlægges lokalt med `scheduleNotificationAsync(..., trigger: null)`, dvs. med det samme og uden et kald til Backend API.

Modulet er implementeret, men **ikke koblet på** appen endnu: `startGeofenceWatch` kaldes ingen steder, og indstillingerne for zone- og tidsadvarsler i `SettingsScreen` er kun lokal skærmtilstand, der ikke gemmes eller læses af modulet. Desuden forventer modulet hver zone som `{polygon: [{latitude, longitude}, ...]}`, mens `/api/zones` returnerer GeoJSON (`[lon, lat]`-ringe, evt. `MultiPolygon`), så der mangler en lille adapter mellem de to. Point-in-polygon-funktionen er heller ikke eksporteret og derfor ikke enhedstestet.

### 5.5.4 Tests og resultater

Mobile Client har ingen automatiserede enheds- eller komponenttests; CI kører kun ESLint (`npm run lint`). Klienten er testet manuelt end-to-end mod en lokalt kørende Backend API via Expo. Backend-loggen fra en sådan session viser bl.a. `POST /api/reports` → `201`, `GET /api/routes` → `200`, `GET /api/reports` og `GET /api/incidents` → `200` (22 gange hver, ved kortbevægelser), `GET /api/crime-index` → `200` og `GET /api/news` → `200`. UC1 og UC2's hovedforløb er dermed gennemført fra appen mod den rigtige backend.

Næste skridt er at tilføje Jest med `jest-expo`, så i hvert fald `isInsidePolygon`, fejlbeskedhåndteringen i `api.request` og dedupliceringen i `geocoding` kan testes isoleret.

### 5.5.5 Delkonklusion

Mobile Client er opbygget med en klar adskillelse mellem skærme, genbrugelige komponenter, delt tilstand i contexts og services, der indkapsler al kommunikation med Backend API, Nominatim og telefonens OS. UC1 og UC2 er implementeret fuldt ud og verificeret manuelt mod den rigtige backend, og NF9 (rute uden login) er overholdt. Den klientlokale geofencing, som er arkitekturens centrale valg for F5 og NF3, er implementeret som modul, men skal kobles på kortskærmen sammen med zonevisningen (F7) og en GeoJSON-adapter, før F5 er opfyldt.
