# 4. Systemarkitektur

## 4.1 Introduktion

Dette kapitel præsenterer SafeRoutes overordnede arkitektur set fra et strukturelt perspektiv, som grundlag for detaildesignet af de enkelte delsystemer i senere kapitler. Afsnit 4.2 fastlægger systemets ydre grænser og dets relationer til eksterne systemer. Afsnit 4.3 analyserer, hvilke af de ikke-funktionelle krav fra kapitel 3 der udgør en arkitektonisk risiko for den domænemodelbaserede tilgang, og hvordan arkitekturen tilpasses for at reducere dem. Afsnit 4.4 præsenterer den resulterende struktur: delsystemerne, hvordan de skal interagere, hvilke grænseflader og protokoller de skal dele, hvordan data planlægges persisteret, og hvilken teknologistack delsystemerne realiseres med, sammenholdt med de oplagte alternativer. Kapitlet forholder sig udelukkende til den strukturelle arkitektur og tager ikke stilling til det interne design af de enkelte delsystemer; det er genstand for kapitel 5.

## 4.2 Systemets ydre grænser og relationer

SafeRoute afgrænses til mobilklienten og backend'en tilsammen; det, brugeren opfatter som "appen", er begge dele. Systemet har fire eksterne relationer, som det ikke selv kontrollerer:

- **OSRM** (Open Source Routing Machine) leverer den rå ruteberegning (geometri og gangtid) mellem to punkter. SafeRoute tilføjer selv trygsedsscoren oven på OSRM's ruteforslag; OSRM ved intet om tryghed.
- **Offentlige datakilder** (bl.a. Danmarks Statistik) leverer kommunale kriminalitetsrater, som indgår i beregningen af zoner og trygsedsscorer.
- **Nyhedskilder** leverer kriminalitetsrelaterede nyheder via RSS/API til nyhedsfeedet og som et supplerende signal til scoringen.
- **OS-notifikationstjenesten** (Expo/Apple/Google's push-infrastruktur) er det lag, SafeRoute i sidste ende afsender og viser notifikationer igennem, uanset om notifikationen er udløst lokalt på telefonen eller (i et fremtidigt scenarie) sendt fra serveren.

Figur 4.1 viser systemgrænsen og disse fire relationer. Et vigtigt arkitekturvalg er allerede indlejret i figuren og uddybes i afsnit 4.3: mobilklienten er en del af systemet, ikke en ekstern klient til en ren server-arkitektur, fordi geofence-logikken (condition'en, der udløser en push-notifikation under en gåtur) bevidst er placeret på telefonen frem for på backend'en.

*Figur 4.1: Systemgrænse og eksterne relationer (se `systemgraense.puml`).*

## 4.3 Analyse af arkitektur

Den indledende, domænemodelbaserede tilgang fra kapitel 3 ("Backend gør alting, klienten viser det") holder ikke, når den holdes op mod de ikke-funktionelle krav. Risikoen er ikke isoleret til én funktion: den opstår, hver gang et NF-krav rammer et sted i arkitekturen, hvor den enkle løsning enten er for langsom, for sårbar over for en enkelt ekstern afhængighed, eller lækker mere data, end den behøver. Dette afsnit gennemgår fire arkitekturkritiske risici, der tilsammen dækker rutemotoren, realtidsadvarslerne, den community-drevne scoring og privatlivslaget, altså de fire delsystemer, der introduceres i figur 4.2, og den arkitekturelle løsning på hver.

### Ruteberegning under belastning (NF1, NF6)

NF1 kræver, at en ruteforespørgsel, inklusive trygsedsscore for alle forslag, besvares inden for 10 sekunder ved op til 2 samtidige forespørgsler pr. sekund. De 10 sekunder er rigeligt til at dække én enkelt forespørgsels egen behandlingstid, selv med live model-inferens pr. vejsegment for hvert ruteforslag:

```
3 ruteforslag × ca. 100 vejsegmenter/forslag = 300 segmenter pr. forespørgsel
300 segmenter × 5 ms model-inferens/segment ≈ 1.500 ms scoringstid pr. forespørgsel
```

1,5 sekund er langt under budgettet, men NF1 stiller ikke kun krav til én forespørgsels egen svartid, den stiller krav til, at systemet kan *følge med* op til 2 forespørgsler i sekundet, løbende. Beregnes scoringen synkront og serielt (én forespørgsel ad gangen), kan backend'en højst nå ca. 1.500 ms⁻¹ ≈ 0,67 forespørgsler i sekundet, under de 2 forespørgsler i sekundet, NF1 kræver. Ankommer forespørgslerne hurtigere, end de kan behandles, vokser køen ubegrænset, og selv en generøs 10-sekundersgrænse pr. forespørgsel bliver til sidst overskredet af ventetiden i køen alene, ikke af selve beregningen: et gennemløbsproblem, ikke et enkelt-forespørgsel-latensproblem. Samtidig gør OSRM's rolle som en enkelt, ekstern rutemotor NF6's krav om 99,5% oppetid til en risiko, hvis backend'en afhænger direkte af én instans uden fallback.

**Løsning:** scoringen flyttes ud af den synkrone forespørgselsvej. Trygsedsscoren for et vejsegment genberegnes periodisk af en asynkron proces (målsat til hvert 15. minut, se Async Worker i afsnit 4.4) og gemmes i Datalaget, så en ruteforespørgsel kun skal slå allerede beregnede scorer op via et indekseret geospatialt opslag, ikke køre model-inferens. Et sådant opslag tager typisk under 10 ms, hvilket løfter den teoretiske gennemløbskapacitet til et par hundrede forespørgsler i sekundet, langt over de 2/s, NF1 kræver, og dermed forsvinder kørisikoen, uanset hvor tæt på grænsen budgettet sættes. NF6-risikoen ved OSRM som enkelt ekstern afhængighed reduceres ved, at Backend API falder tilbage på en lokal, forenklet ruteberegning, hvis OSRM ikke svarer (NF7), og ved at OSRM selvhostes som en container i driftsmiljøet (figur 4.3) frem for at afhænge af en offentlig demo-instans uden driftsgaranti.

### Geofence-baseret notifikation vs. serverstyret push (NF3, NF11)

F5 kræver, at en bruger advares, både ved indtræden i et utrygt område og på tidspunkter, hvor utryghed historisk stiger, mens en gåtur er i gang. NF3 stiller et konkret krav til, hvor ofte det kan opdages:

```
Positionsopdatering ≥ hvert 15.-30. sekund, eller for hver 25 meter bevægelse
```

Den oplagte arkitektur er at lade Backend modtage brugerens live-position løbende, evaluere den mod zone-polygonerne server-side, og sende en push-notifikation, når en zone krydses. Det ville imidlertid indebære, at telefonen skal streame sin position til serveren med samme frekvens som NF3 kræver, hvilket introducerer to risici:

1. **Latens og robusthed.** Hver zonekontrol ville afhænge af en netværks-roundtrip (position op, evaluering, notifikation ned) plus serverens svartid. Falder forbindelsen ud, eller er den langsom, netop dér hvor en bruger bevæger sig gennem et område uden dækning, forsvinder advarslen i det øjeblik, den er mest nødvendig.
2. **Datamininering.** NF11 stiller krav om, at *aggregerede* positions- og rapportdata anonymiseres med differential privacy, før de indgår i offentligt viste scorer. Selvom NF11 formelt kun dækker de data, der bliver *offentligt* synlige, ville en løbende server-side positions-stream i praksis betyde, at systemet opbygger en detaljeret, tidsstemplet bevægelseshistorik pr. bruger, præcis den type data, differential privacy-laget er designet til at undgå at eksponere. At undgå at indsamle data, man ikke har brug for at gemme, er en billigere og mere robust beskyttelse end at anonymisere det bagefter.

**Løsning:** geofence-evalueringen er lagt som en lokal condition på telefonen, ikke som et server-kald. Mobilklienten henter zone-polygonerne (`GET /api/zones`, evt. suppleret af `/ws/zones`) og cacher dem lokalt; `Location.watchPositionAsync` (interval 15 sek. / 25 m, jf. NF3 direkte) evaluerer herefter to conditions lokalt for hver ny position: (a) et point-in-polygon-tjek mod de cachede rødzoner, og (b) et tidspunkt-tjek mod en fast tidsramme. Er en condition opfyldt, planlægges notifikationen direkte via telefonens eget notifikations-API, uden en tur til Backend. Dette reducerer risikoen på to måder: advarslens latens bliver bundet af telefonens egen positionsopdatering (NF3), ikke af en netværksforbindelse, og Backend modtager aldrig en løbende strøm af brugerens position under en gåtur, kun de positioner, brugeren selv aktivt sender via ruteopslag eller en hændelsesrapport. Figur 4.5 (afsnit 4.4.1) viser flowet.

Denne løsning har en bevidst begrænsning: den dækker kun conditions, klienten selv kan afgøre ud fra allerede hentede data (position, cachede polygoner, klokkeslæt). Et scenarie som "en anden bruger har lige indrapporteret og fået bekræftet en hændelse 50 meter foran dig, mens du går" kræver, at Backend selv kan initiere en notifikation, hvilket er årsagen til, at "OS-notifikationstjeneste" fortsat indgår som en ekstern relation i figur 4.1 og som en planlagt server→klient-kant i containerdiagrammet (figur 4.2): den dækker den serverinitierede sti, mens den klientlokale sti dækker den almindelige, latenskritiske sti.

### Frisk trygsedsscore fra bekræftede indrapporteringer (NF4, NF5)

F3 kræver, at en indrapportering skal bekræftes af flere nærliggende brugere, før den vægtes fuldt i trygsedsscoren. To krav rammer forskellige led i den kæde, og skal derfor ikke løses med den samme mekanisme: NF4 kræver, at en ny, ubekræftet rapport er *synlig* for andre brugere inden for 1 minut; NF5 kræver, at en rapport, der opnår tilstrækkelig verifikation, kan *påvirke den viste trygsedsscore* inden for 5 minutter.

NF4 opfyldes af den simple del af arkitekturen: `GET /api/reports` læser rapporter direkte fra Datalaget, så en ny rapport bliver synlig for andre klienter, næste gang de forespørger, typisk sekunder efter indsendelse. NF5 er derimod en reel arkitektonisk risiko, hvis den holdes op mod den asynkrone scoringsproces fra det foregående punkt: trygsedsscoren genberegnes af Async Worker på en fast periode, sat til hvert 15. minut. En rapport, der lige er blevet tilstrækkeligt bekræftet, kan i værste fald vente op til 15 minutter på at slå igennem i den viste score, tre gange længere end NF5 tillader.

**Løsning:** den periodiske genberegning bevares til at indfange langsomme, akkumulerede ændringer (nye officielle data, tidspunkt-skift), men suppleres med en event-udløst genberegning: når `POST /api/reports/{id}/confirm` gør en rapport tilstrækkeligt verificeret, sender Backend API et målrettet genberegningsjob for det berørte områdes segmenter til Async Worker, i stedet for at vente på den næste periodiske kørsel. Det holder NF5's 5-minuttersbudget uafhængigt af, hvor langt det periodiske interval er sat, uden at hver enkelt bekræftelse skal udløse en fuld genberegning af hele byen.

### Placering af differential privacy-laget (NF11, NF13)

NF11 kræver, at aggregerede positions- og rapportdata, der indgår i offentligt viste trygsedsscorer eller heatmaps, anonymiseres med en Laplace-baseret differential privacy-mekanisme (epsilon ≤ 1,0); NF13 kræver, at behandlingen i øvrigt overholder GDPR. Selve DP-mekanismen er ukompliceret, men *hvor i arkitekturen* den skal kaldes, er en arkitekturkritisk beslutning i sig selv: mekanismen trækker et nyt, tilfældigt støjtal ved hvert kald. Kaldes den ved hver enkelt læsning af en offentlig score, f.eks. inde i selve `GET /api/zones`-endpointet, vil to på hinanden følgende opslag på samme zone returnere to forskellige støjede tal for den samme underliggende sande værdi. En bruger, der forespørger det samme endpoint mange gange, kan da gennemsnitliggøre støjen væk og tilnærme den ustøjede værdi, et klassisk "averaging attack" mod differential privacy, der reelt underminerer NF11, selvom mekanismen teknisk set anvendes.

**Løsning:** DP-støjen skal lægges på én gang, på skrivetidspunktet, når en aggregeret statistik beregnes og caches, samme sted som den periodiske og event-udløste genberegning fra ovenstående punkt allerede skriver til Datalaget. Alle efterfølgende læsninger af den offentlige API returnerer dermed den samme, allerede-støjede værdi, indtil næste genberegning, hvilket lukker averaging-angrebet uden at ændre selve DP-mekanismen. Dette optages her som en eksplicit arkitekturbeslutning, der skal respekteres, når scoringspipelinen i Async Worker implementeres, frem for at overlade placeringen til den enkelte udvikler at opdage undervejs.

## 4.4 Systemets struktur og grænseflader

Analysen i afsnit 4.3 giver fire delsystemer, vist som et container-diagram i figur 4.2: **Mobile Client** (React Native/Expo), **Backend API** (FastAPI, REST + WebSocket), **Async Worker** og et fælles **Datalag** (PostgreSQL/PostGIS). Mobile Client og Backend API er de eneste delsystemer, brugeren interagerer direkte eller indirekte med; Async Worker og Datalag understøtter dem. Den planlagte teknologi til hvert delsystem begrundes i afsnit 4.4.4.

Async Worker's realisering afhænger bevidst af belastningen, systemet reelt skal bære. Ved den skala, NF1 lægger op til (op til 2 samtidige forespørgsler i sekundet, jf. afsnit 4.3), kan de periodiske og event-udløste opgaver (genberegning af trygsedsscorer, nyhedsindsamling) afvikles som en enkelt, planlagt baggrundsproces, der kører sammen med Backend API, uden behov for en selvstændig kø-infrastruktur. Vokser belastningen, eller skal flere Backend API-instanser dele arbejdet og broadcaste zoneopdateringer til hinanden over `/ws/zones`, udskilles Async Worker til en kø-baseret løsning (f.eks. Celery med Redis som broker), uden at grænsefladerne til de øvrige delsystemer ændres. Denne skalerbarhed er selve pointen med at holde Async Worker som et selvstændigt delsystem i figur 4.2, uafhængigt af hvilken af de to realiseringer der vælges ved lancering.

Figur 4.3 viser, hvordan delsystemerne kan allokeres til driftsmiljøet: Backend API og Async Worker deployeres som to containere på en applikationsserver, PostgreSQL/PostGIS som en container på en database-server (suppleret af Redis, hvis Async Worker udskilles til en kø-baseret løsning), OSRM som en selvstændig, selvhostet container, og Mobile Client afvikles på brugerens egen telefon.

*Figur 4.2: Arkitektur (container-diagram) (se `arkitektur-containere.puml`).*

*Figur 4.3: Allokering af arkitektur (deployment-diagram) (se `deployment.puml`).*

### 4.4.1 Interaktion mellem delsystemer

Figur 4.4 viser interaktionen for UC1 (Find og vælg tryg rute, jf. kapitel 3): Mobile Client forespørger Backend API, som selv forespørger OSRM for rutegeometri og slår tryghedsscorer op i Datalaget, før det samlede ruteforslag returneres.

Figur 4.5 viser interaktionen bag F5's geofence- og tidsbaserede advarsler, jf. arkitekturvalget i afsnit 4.3: Mobile Client henter zone-polygonerne én gang (eller abonnerer på ændringer via `/ws/zones`), hvorefter begge conditions, zoneindtræden og klokkeslæt, evalueres lokalt for hver positionsopdatering, uden yderligere kald til Backend API.

*Figur 4.4: Systemsekvensdiagram, UC1: Find og vælg tryg rute (se `seq-uc1-rute.puml`).*

*Figur 4.5: Systemsekvensdiagram, geofence som condition for push-notifikation (se `seq-geofence.puml`).*

### 4.4.2 Interfaces og protokoller

**Mobile Client ↔ Backend API.** Grænsefladen er REST over HTTP(S) med JSON, suppleret af én WebSocket-kanal (`/ws/zones`) til løbende zone-/scoreopdateringer. Alle skrivende kald, der kræver et login (bl.a. `POST /api/reports`), skal godkendes via en `Authorization: Bearer <token>`-header med et signeret, tidsbegrænset token (JWT), jf. NF13's krav om lovlig databehandling. Tabel 4.1 opsummerer de vigtigste endpoints.

**Tabel 4.1: Udvalgte REST-endpoints mellem Mobile Client og Backend API**

| Metode | Endpoint | Formål | Krav |
|---|---|---|---|
| `GET` | `/api/routes?from=&to=&mode=` | Ruteforslag med tid + trygsedsscore | F1, NF1 |
| `GET` | `/api/zones?bbox=` | Zone-polygoner farvekodet efter tryghed | F7 |
| `GET`/`POST` | `/api/reports` | Hente/indsende hændelsesrapporter | F2 |
| `POST` | `/api/reports/{id}/confirm` | Verificere andres rapport | F3 |
| `GET` | `/api/crime-index?city=` | Bytryghedsoversigt | F4 |
| `GET` | `/api/news?city=` | Kriminalitetsrelateret nyhedsfeed | F9 |
| `WS` | `/ws/zones` | Løbende push af score-/zoneændringer | F5 |

Et konkret svar fra `GET /api/routes` har formen:

```json
{
  "duration_minutes": 34.2,
  "distance_meters": 2650,
  "safety_score": 8.6,
  "safety_label": "very safe",
  "geometry": { "type": "LineString", "coordinates": [[10.21, 56.15], ...] }
}
```

**Backend API ↔ OSRM.** REST over HTTP mod OSRM's eget "Route"-endpoint (`/route/v1/foot/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson&alternatives=true`), som returnerer GeoJSON-rutegeometri og varighed for én eller flere alternative ruter. SafeRoute tilføjer selv trygsedsscoren oven på dette svar; OSRM leverer udelukkende geometri og tid.

**Backend/Worker ↔ eksterne datakilder.** Både de offentlige kriminalitetsdata og nyhedskilderne tilgås som periodisk pull over HTTP (hhv. hver 6. time og hvert 15. minut), ikke push. Fordi disse kilder er uden for systemets kontrol, gælder NF7 direkte for denne grænseflade: er én kilde midlertidigt utilgængelig ved et opdateringsforsøg, beholder systemet det senest cachede resultat og fejler ikke ruteforespørgsler eller kortvisning som følge heraf.

**Mobile Client ↔ OS-notifikationstjeneste.** Klienten planlægger og viser lokale, øjeblikkelige notifikationer direkte via telefonens eget notifikations-API, som beskrevet i afsnit 4.3. Samme grænseflade bruges også til en serverinitieret variant (Backend sender til et push-API med et per-enhed push-token), til de conditions kun serveren kender.

### 4.4.3 Datamodeller og persistering

Datalaget realiseres som PostgreSQL med PostGIS-udvidelsen, så geospatiale forespørgsler (nærhedssøgning, rute-mod-polygon-forespørgsler til zoner, bbox-filtrering) kan udnytte native `GEOGRAPHY`-typer og `GIST`-indekser i stedet for at beregne dem i applikationslaget. De fire centrale entiteter er:

- **Incident**: et enkelt kriminalitets-/hændelsespunkt, tagget med kilde (`official` / `community` / `news`) og verifikationsstatus.
- **SegmentScore**: den forudberegnede trygsedsscore pr. vejsegment og tidsbucket (dag/aften/nat), med et felt til forklaringen (SHAP-værdier) bag scoren (NF8).
- **Report**: en brugerindsendt realtidsrapport, koblet til en bruger og med et løbende bekræftelsestal.
- **User**: kontoen, dens risikoprofil og nødkontakter.

Nyhedsartikler arkiveres separat i Datalaget, fordi RSS-feeds i sig selv ikke har nogen historik: uden en lokal arkivering ville systemet ikke kunne vise andet end de seneste ét til to dages nyheder.

### 4.4.4 Planlagt teknologistack

Teknologistacken er endnu ikke endeligt fastlagt; dette afsnit beskriver den stack, der planlægges anvendt, og begrunder den. Risikoanalyserne i afsnit 4.3 og strukturen ovenfor stiller en række konkrete krav til teknologien: asynkron I/O med WebSocket (NF1, `/ws/zones`), samme sprog som scoringsmodellen (NF8), én kodebase til iOS og Android med baggrundslokation og lokale notifikationer (NF3, NF14), native geospatiale forespørgsler (afsnit 4.4.3) og en rutemotor, systemet selv kan drifte (NF6, NF7). For hvert delsystem sammenlignes den planlagte teknologi med de oplagte alternativer ud fra netop disse krav, så planen kan justeres, hvis forudsætningerne ændrer sig, inden den endelige beslutning træffes.

**Backend API: FastAPI (Python)**

| Alternativ | Styrke | Afgørende svaghed for SafeRoute |
|---|---|---|
| **FastAPI** (planlagt) | Asynkron (ASGI) fra bunden, indbygget WebSocket, automatisk validering og OpenAPI-dokumentation via Pydantic [1][2] | Pythons GIL begrænser CPU-tung parallelisme [3]; mindre "batteries included" end Django/Spring |
| Django + DRF | Modent ORM, admin-panel og autentificering indbygget | Async kræver ASGI, og ORM'et understøtter ikke transaktioner i async-kode; WebSocket kræver tilføjelsen Django Channels [4] |
| Flask | Simpelt og letvægts | WSGI: hver forespørgsel binder én worker, også ved `async`-views, og baggrundsopgaver kan ikke startes med `asyncio.create_task` [5]; ingen indbygget WebSocket eller validering |
| Node.js (Express/NestJS) | Stærk asynkron I/O og WebSocket-understøttelse | Scoringsmodellen (scikit-learn, SHAP) er Python; det ville kræve en ekstra Python-tjeneste og en sprogovergang mellem API og model |
| Spring Boot (Java) | Meget modent værktøj til sikkerhed og ORM, også geospatialt (Hibernate Spatial) | Tungere at udvikle i ved projektets skala; svagt ML-økosystem i forhold til Python |

FastAPI planlægges anvendt, fordi det er det eneste alternativ, der opfylder begge de tungeste krav på én gang: asynkron håndtering af REST, WebSocket og baggrundsopgaver i samme proces, *og* samme sprog som scoringsmodellen, så API og scoringskode vil kunne dele biblioteker. Node.js matcher det første krav og Django/Spring bedre det modne værktøj, men ingen af dem uden at splitte systemet i to sprog. GIL-begrænsningen vurderes at være acceptabel, fordi den CPU-tunge scoring i forvejen er planlagt flyttet ud af forespørgselsvejen (afsnit 4.3).

**Mobile Client: React Native med Expo**

| Alternativ | Styrke | Afgørende svaghed for SafeRoute |
|---|---|---|
| **React Native + Expo** (planlagt) | Én JavaScript-kodebase til iOS og Android; færdige moduler til lokation i baggrunden og geofencing (`expo-location`) [6], planlagte lokale notifikationer (`expo-notifications`) [7] og sikker token-lagring (`expo-secure-store`) | Mindre kontrol over native kodestier; det administrerede workflow kan halte efter de nyeste platforms-API'er |
| Flutter (Dart) | Én kodebase, god rendering-performance | Nyt sprog (Dart) for teamet; lokation og geofencing afhænger af tredjeparts-plugins frem for en samlet, administreret SDK |
| Native (Swift + Kotlin) | Fuld kontrol over baggrundslokation og notifikationer | To kodebaser at udvikle og vedligeholde; direkte i modstrid med NF14 ved projektets ressourcer |
| Progressiv webapp (PWA) | Ingen app-butik, én webkodebase | Geolocation API'et leverer kun positioner, mens siden er synlig [8], og web-push på iOS kræver iOS 16.4+ og at appen er føjet til hjemmeskærmen [9]; geofence-advarslen under en gåtur (F5, NF3) kan derfor ikke realiseres |

React Native med Expo planlægges anvendt, fordi den klientlokale geofence-arkitektur fra afsnit 4.3 står og falder med pålidelig lokationsovervågning og lokale notifikationer på *begge* platforme. Det udelukker en PWA, og native udvikling fravælges på grund af NF14's dobbelte vedligeholdelsesbyrde. Mellem Flutter og React Native forventes udslaget at være, at Expo leverer de præcise moduler, arkitekturen skal bruge, som én samlet og versionsafstemt SDK, og at JavaScript/React er samme værktøj, som også vil gøre en webversion mulig (`react-native-web`).

**Datalag: PostgreSQL med PostGIS**

| Alternativ | Styrke | Afgørende svaghed for SafeRoute |
|---|---|---|
| **PostgreSQL + PostGIS** (planlagt) | Bredeste udvalg af geospatiale funktioner (`GEOGRAPHY`, `ST_Intersects`, `ST_DWithin`) med GIST-indeks [10]; fuld relationel model og transaktioner | Kræver indeksering og tuning; administreret hosting med PostGIS er mindre udbredt og dyrere |
| MongoDB | `2dsphere`-indeks og fire geo-operatorer (`$geoWithin`, `$geoIntersects`, `$near`, `$nearSphere`) [11] | Svagere til de relationelle data (bruger → rapporter → bekræftelser) og snævrere geospatialt funktionsudvalg |
| MySQL (spatial) | Udbredt; har spatial-typer og spatiale indeks [12] | Færre geospatiale funktioner end PostGIS [10][12] |
| SQLite (evt. SpatiaLite) | Ingen server, én fil, nul drift | Kun én skriver ad gangen; dokumentationen anbefaler selv en klient/server-database ved mange samtidige skrivere [13], hvilket rammer samtidige rapporter fra mange brugere (NF4) |

PostgreSQL/PostGIS planlægges anvendt, fordi datamodellen i afsnit 4.4.3 er *både* relationel (brugere, rapporter, bekræftelser) *og* geospatial (segmenter, zoner, nærhed), og PostGIS er det eneste alternativ, der dækker begge fuldt ud. Det vil gøre det muligt at lave rute-mod-polygon- og nærhedsforespørgsler i databasen med indeks i stedet for i applikationslaget, hvilket er forudsætningen for de hurtige opslag under 10 ms i afsnit 4.3.

**Rutemotor: OSRM (selvhostet)**

| Alternativ | Styrke | Afgørende svaghed for SafeRoute |
|---|---|---|
| **OSRM** (planlagt) | Meget hurtige forespørgsler takket være en forudberegnet graf (Contraction Hierarchies) [14][15], simpelt HTTP-API med alternative ruter (`alternatives=true`) [16], open source og selvhostbar | Vægte fastlægges ved forudberegningen, så tryghed kan ikke indgå direkte i ruteomkostningen; grafen skal genopbygges fra OSM-udtræk |
| GraphHopper | Open source, gå-profil, "custom models" kan vægte ruter pr. forespørgsel [17] | Java-tjeneste med højere hukommelsesforbrug; fleksibiliteten er ikke nødvendig, så længe scoringen lægges oven på ruteforslagene |
| Valhalla | Open source, dynamisk omkostningsfunktion ved forespørgselstidspunktet [18] | Mere kompleks opsætning og tuning end OSRM |
| Google / Mapbox Directions API | Ingen drift, høj kvalitet og dækning | Betaling pr. forespørgsel [19], ratebegrænsninger og licensvilkår for lagring/kombination af data; systemet bliver afhængigt af én ekstern udbyder (NF6) |

OSRM planlægges anvendt, fordi arkitekturen bevidst adskiller *ruteberegning* fra *trygsedsscoring*: OSRM skal kun levere et par hurtige ruteforslag, som Backend API derefter scorer ud fra de forudberegnede segmentscorer (afsnit 4.3). Til den opgave vurderes OSRM at være den hurtigste og simpleste selvhostbare motor, og selvhosting vil fjerne den afhængighed af en kommerciel udbyder, som NF6 og NF7 gør til en risiko. Ønsker man senere, at tryghed skal påvirke selve rutevalget, og ikke kun rangeringen af forslag, er GraphHopper eller Valhalla det naturlige skift, fordi de kan vægte ruter pr. forespørgsel.

**Async Worker: enkelt baggrundsproces frem for Celery/Redis ved lancering**

| Alternativ | Styrke | Afgørende svaghed for SafeRoute |
|---|---|---|
| **Enkelt, tidsstyret baggrundsproces** (planlagt ved lancering) | Ingen broker at deploye; få bevægelige dele | Skalerer ikke ud over én proces; ingen automatisk genkørsel af afbrudte jobs |
| Celery + Redis (målarkitektur ved vækst) | Horisontal skalering, genkørsel af jobs, planlægning (Celery Beat) [20]; Redis kan også bruges til broadcast mellem API-instanser på `/ws/zones` | Ekstra infrastruktur at drifte og overvåge, som ikke er nødvendig ved NF1's belastning |
| RQ / APScheduler | Enklere end Celery | RQ kræver stadig Redis; APScheduler giver ingen fordeling på tværs af processer |
| Cron-job | Simpelt og velkendt | Kan ikke modtage de event-udløste genberegningsjobs fra `POST /api/reports/{id}/confirm` (NF5) |

En enkelt baggrundsproces planlægges ved lancering, fordi den forventes at dække både de periodiske og de event-udløste jobs (afsnit 4.3) ved den belastning, NF1 lægger op til, uden ekstra infrastruktur. Celery med Redis er den planlagte realisering, hvis belastningen eller antallet af Backend API-instanser vokser, og skiftet vil kunne ske uden at ændre grænsefladerne til de øvrige delsystemer (afsnit 4.4).

### Kilder til afsnit 4.4.4 (skal formateres til referencelisten)

Alle webkilder tilgået 28.09.2026.

1. FastAPI-dokumentation, "Concurrency and async / await". https://fastapi.tiangolo.com/async/
2. FastAPI-dokumentation, "WebSockets". https://fastapi.tiangolo.com/advanced/websockets/
3. Python Software Foundation, *Python Glossary*, opslag "global interpreter lock". https://docs.python.org/3/glossary.html#term-global-interpreter-lock
4. Django-dokumentation, "Asynchronous support". https://docs.djangoproject.com/en/stable/topics/async/
5. Flask-dokumentation, "Using async and await". https://flask.palletsprojects.com/en/stable/async-await/
6. Expo-dokumentation, "Location" (`expo-location`). https://docs.expo.dev/versions/latest/sdk/location/
7. Expo-dokumentation, "Notifications" (`expo-notifications`). https://docs.expo.dev/versions/latest/sdk/notifications/
8. W3C, *Geolocation* (W3C Recommendation), afsnit 6.5 "Request a position" og 6.6 "Acquire a position". https://www.w3.org/TR/geolocation/
9. WebKit, "Web Push for Web Apps on iOS and iPadOS" (2023). https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/
10. PostGIS-dokumentation, kap. 4 "Data Management" (afsnit om Geography-typen og spatiale indeks). https://postgis.net/docs/using_postgis_dbmanagement.html
11. MongoDB-dokumentation, "Geospatial Queries". https://www.mongodb.com/docs/manual/geospatial-queries/
12. MySQL 8.4 Reference Manual, "Spatial Analysis Functions". https://dev.mysql.com/doc/refman/8.4/en/spatial-analysis-functions.html
13. SQLite, "Appropriate Uses For SQLite". https://www.sqlite.org/whentouse.html
14. Luxen, D. & Vetter, C. (2011). "Real-time routing with OpenStreetMap data". *Proceedings of the 19th ACM SIGSPATIAL International Conference on Advances in Geographic Information Systems*, s. 513–516.
15. Geisberger, R., Sanders, P., Schultes, D. & Delling, D. (2008). "Contraction Hierarchies: Faster and Simpler Hierarchical Routing in Road Networks". *Experimental Algorithms (WEA 2008)*, LNCS 5038, s. 319–333. Springer.
16. Project OSRM, "OSRM API Documentation" (v5.24.0), Route service. https://project-osrm.org/docs/v5.24.0/api/
17. GraphHopper, "Custom Models". https://github.com/graphhopper/graphhopper/blob/master/docs/core/custom-models.md
18. Valhalla-dokumentation. https://valhalla.github.io/valhalla/
19. Google Maps Platform, "Pricing". https://mapsplatform.google.com/pricing/
20. Celery-dokumentation, "Periodic Tasks". https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
