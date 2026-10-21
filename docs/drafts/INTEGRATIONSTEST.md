# 6. Integrationstest

## 6.1 Introduktion

Kapitel 5 verificerede hvert delsystem for sig, med eksterne afhængigheder erstattet af mocks. Dette kapitel verificerer, at delsystemerne fungerer *sammen* gennem de grænseflader, arkitekturen i kapitel 4 fastlagde (tabel 4.1): Mobile Client mod Backend API, og Backend API mod OSRM, Datalaget og de eksterne datakilder. Testene er tekniske og udføres uden brugergrænseflade. De skal give sikkerhed for, at grænsefladerne og de arkitekturkritiske ikke-funktionelle krav (NF1, NF4, NF7) holder, når de rigtige komponenter kobles sammen.

## 6.2 Teststrategi

Integrationstesten er **use case-drevet** og bygger **bottom-up** oven på kapitel 5: delsystemernes interne logik er allerede testet isoleret, så her testes kun samspillet. For hver af de to Must have-use cases (UC1 og UC2) gennemløbes hovedforløbet og de vigtigste udvidelser via de kald, appen selv foretager.

Der bruges ingen mocks. Testen driver Mobile Client's rigtige service-lag (`mobile/src/services/api.js` og `geocoding.js`, uændret) mod en kørende Backend API, som selv kalder den rigtige OSRM, Danmarks Statistik, RSS-feeds og Datalaget. Den eneste bevidste fejlinjektion er en ekstra Backend-instans uden adgang til OSRM, som bruges til at teste NF7. Brugergrænsefladen (skærme og komponenter) indgår ikke; den er testet manuelt (afsnit 5.5.4).

## 6.3 Integrationstest af UC1 og UC2

### 6.3.1 Opstilling

Opstillingen er vist i figur 6.1. Testen er udført 5. oktober 2026 på en udviklermaskine (Windows 10, Python 3.13, Node 22.14):

- **Backend API** startes med `tests/integration/serve.py`: på port 8001 med den konfigurerede OSRM (`routing.openstreetmap.de`), på port 8002 med OSRM sat til en lukket port og (i gentesten, afsnit 6.5) på port 8003 mod en OSRM, der accepterer forbindelsen men aldrig svarer. Alle instanser kører Async Worker's løkker, så zone- og nyhedsdata er rigtige. SQLite-filerne omdirigeres til en midlertidig mappe, så testdata ikke havner i udviklingsdatabasen.
- **Testdriveren** `tests/integration/run.mjs` importerer `api.js` flere gange som separate modulinstanser. Hver instans svarer til én telefon med sin egen base-URL og sit eget login-token. Node 22 har indbygget `fetch` og `WebSocket`, så modulet kører uden ændringer.
- Svartider måles i testdriveren, dvs. inklusive HTTP-overhead, som klienten oplever dem.

*Figur 6.1: Opstilling for integrationstest (se `integrationstest-opstilling.puml`).*

### 6.3.2 Resultater

**Tabel 6.1: Integrationstest af UC1, Find og vælg tryg rute**

| ID | Grænseflade | Test | Resultat | Status |
|---|---|---|---|---|
| I1.1 | Mobile → Nominatim | `searchPlaces("Aarhus H")` | Nominatim svarede `HTTP 403`; funktionen returnerede en tom liste uden fejl | ✗ |
| I1.2 | Mobile → Backend → OSRM | `getRoutes` Aarhus H → Universitetsparken | 2 rigtige ruteforslag: 39,8 min/2.975 m og 42,5 min/3.183 m (180 og 194 koordinater) | ✓ |
| I1.3 | Backend → Mobile | `RouteOption`-kontrakten | Score i [1; 10], gyldig label, hurtigst først, GeoJSON i `[lon, lat]` med start ved Aarhus H | ✓ |
| I1.4 | Backend → OSRM (nede) | Fallback, NF7 | `200` med 2 lige-linje-forslag | ✓ |
| I1.5 | Mobile → Backend → OSRM | NF1: 20 forespørgsler efter hinanden | Median 676 ms, maks. 776 ms | ✓ |
| I1.6 | Mobile → Backend → OSRM | NF1: 2 forespørgsler/s i 15 s (30 i alt) | Alle besvaret, men median 10,9 s, maks. 15,8 s; 17 af 30 over 10 s | ✗ |
| I1.7 | Backend → OSRM (timeout) | Svartid, når OSRM ikke svarer | Fallback returneret efter 10,7 s | ✗ |

**Tabel 6.2: Integrationstest af UC2, Indrapportér hændelse**

| ID | Grænseflade | Test | Resultat | Status |
|---|---|---|---|---|
| I2.1 | Mobile → Backend | `submitReport` uden login (udvidelse 3a) | Afvist; appen får beskeden "Login required to do that" | ✓ |
| I2.2 | Mobile → Backend → Datalag | `signup` → `setAuthToken` → `submitReport` | `201`, `confirmations = 0`, intet `user_id` i svaret | ✓ |
| I2.3 | Datalag → Backend → anden telefon | NF4: rapporten synlig for en anden klient uden login | Synlig efter 8 ms; intet `user_id` | ✓ |
| I2.4 | Mobile → Backend | Login med forkert adgangskode | Appen får "Invalid email or password" | ✓ |
| I2.5 | Mobile → Backend | Ugyldig rapport (mangler koordinater) | `422` omsat til læsbar tekst ("Field required; Field required") | ✓ |
| I2.6 | Mobile → Backend → Datalag | Anden bruger bekræfter rapporten (F3) | `confirmations` 0 → 1 | ✓ |
| I2.7 | Mobile → Backend → Datalag | Samme bruger bekræfter igen | Accepteret, `confirmations` 1 → 2 | ✗ |

**Tabel 6.3: Øvrige grænseflader**

| ID | Grænseflade | Resultat | Status |
|---|---|---|---|
| I3.1 | Mobile → Backend → DST-cache (`getZones`) | 311 kommunepolygoner cachet ved opstart; 3 i Aarhus-bbox'en | ✓ |
| I3.2 | Mobile ↔ Backend WebSocket (`openZonesFeed`) | Besked modtaget efter ca. 5 s (syntetiske data, jf. afsnit 5.2.4) | ✓ |
| I3.3 | Mobile → Backend → RSS + arkiv (`getNews`) | 200 nyheder, 160 med position | ✓ |

I alt blev 17 tests gennemført, og 13 bestod. Testdriveren kan genkøres med `node tests/integration/run.mjs`, når de to backend-instanser kører. I1.7 og kontrolmålingerne i afsnit 6.4 er målt separat med samme forespørgsel.

## 6.4 Diskussion

**NF1 og OSRM.** Én ruteforespørgsel ad gangen tager under et sekund (I1.5), men ved 2 forespørgsler i sekundet vokser svartiden til over 10 sekunder (I1.6). Flaskehalsen er OSRM og ikke Backend API. Det viser to kontrolmålinger med samme belastning: kaldt direkte fra testmaskinen gav den offentlige OSRM-instans forbindelsestimeout på alle 30 forespørgsler. Med OSRM slået fra (port 8002) svarede Backend API derimod med en flad svartid på 2,9–3,9 s, uden at køen voksede, så den asynkrone forespørgselsvej følger med belastningen. De ca. 3 s skyldes, at Windows bruger omkring 2 s på at afvise en forbindelse til en lukket port; det er ikke beregningstid. Efter testen holdt den offentlige instans helt op med at svare testmaskinen, sandsynligvis på grund af rate limiting. Resultatet bekræfter dermed risikoanalysen i afsnit 4.2.1: en delt, offentlig rutemotor kan hverken bære NF1 eller NF6, og beslutningen om at selvhoste OSRM (figur 4.3) er nødvendig, ikke kun ønskværdig.

**NF7 virker, men for langsomt.** Fallback-mekanismen sikrer, at brugeren altid får et svar (I1.4), men når OSRM ikke svarer i stedet for at afvise forbindelsen, venter Backend API hele sin timeout på 10 s, før fallback'et bruges (I1.7). Det overskrider NF1 i netop den situation, NF7 skal håndtere. Timeouten bør sættes ned til få sekunder.

**Geokodning (I1.1).** Nominatim afviste forespørgslerne fra testmaskinen med `403`. Nominatims brugsbetingelser kræver en identificerende `User-Agent`, og den offentlige instans blokerer aggressivt. Det er ikke afgjort, om en telefon bliver afvist på samme måde, men testen afslørede, at `searchPlaces` skjuler fejlen og returnerer en tom liste. Brugeren ser derfor bare ingen forslag, uden forklaring. Ligesom med OSRM peger det på, at en egen eller betalt geokoder er nødvendig før drift (jf. kommentaren i `geocoding.js`), og at fejlen bør vises i `PlaceSearchInput`.

**UC2.** Hele kæden fra login over indrapportering til visning hos en anden bruger fungerer på tværs af delsystemerne. NF4 (synlig inden for 2 minutter) er opfyldt med stor margin, fordi `GET /api/reports` læser direkte fra Datalaget. Det privatlivsvalg, at `user_id` aldrig sendes til andre brugere, holder hele vejen igennem. Fejlbeskeder fra Backend API, inklusive valideringsfejl, når frem til appen som læsbar tekst. Den eneste fejl, I2.7, bekræfter den mangel, der blev identificeret i kapitel 5: der er ingen dubletkontrol på bekræftelser, så én bruger alene kan få en rapport til at fremstå verificeret (F3).

**Begrænsninger.** Testene kører på én maskine mod en udviklingsserver og siger derfor intet om oppetid (NF6) eller ydelse på en rigtig server. NF5 kunne ikke testes, fordi den event-udløste genberegning ikke er implementeret. WebSocket-testen (I3.2) verificerer kun, at kanalen virker, ikke indholdet.

## 6.5 Gentest efter rettelserne

De tre rettelser fra afsnit 6.4 er implementeret, og samtidig er NF10 og NF8 tilføjet: OSRM-timeouten er sat ned fra 10 til 3 s (`external/osrm.py`), `searchPlaces` kaster nu en læsbar fejl, som `PlaceSearchInput` viser, og identificerer appen over for Nominatim med en `User-Agent`. Bekræftelser gemmes i en tabel med `(report_id, user_id)` som primærnøgle, så samme bruger kun kan bekræfte én gang og aldrig sin egen rapport (F3). Indrapportering er begrænset til 5 rapporter pr. bruger pr. time (NF10, `429`), og hvert ruteforslag har fået et `explanation`-felt (NF8).

Testdriveren blev genkørt 19. oktober 2026 med samme opstilling (figur 6.1), nu med en tredje Backend-instans, hvis OSRM accepterer forbindelsen men aldrig svarer, så I1.7 måles i selve testen. Belastningstestene I1.5 og I1.6 blev ikke gentaget for ikke at belaste den offentlige OSRM-instans igen; de kan køres med `node tests/integration/run.mjs --load`.

**Tabel 6.4: Gentest af de tests, der fejlede, samt nye tests**

| ID | Grænseflade | Test | Resultat | Status |
|---|---|---|---|---|
| I1.1 | Mobile → Nominatim | `searchPlaces("Aarhus H")` | 3 forslag, første: Værkmestergade, Aarhus | ✓ |
| I1.3 | Backend → Mobile | `RouteOption`-kontrakten inkl. forklaring (NF8) | Fx "Passes through Aarhus: 468.7 violent crimes per 100,000/yr (around or below the national average). Street-level factors (lighting, recent reports) are not scored yet." | ✓ |
| I1.7 | Backend → OSRM (hænger) | Svartid, når OSRM ikke svarer | Fallback returneret efter 3,6 s | ✓ |
| I2.7 | Mobile → Backend → Datalag | Samme bruger bekræfter igen | Afvist: "You have already confirmed this report" | ✓ |
| I2.8 | Mobile → Backend | Indsender bekræfter egen rapport (F3) | Afvist: "You can't confirm your own report" | ✓ |
| I2.9 | Mobile → Backend → Datalag | NF10: grænse for antal rapporter | 5 accepteret, derefter `429` "Too many reports — please wait up to 60 minutes …" | ✓ |

Alle 17 funktionelle tests i gentesten bestod (I1.1–I1.4, I1.7, I2.1–I2.9, I3.1–I3.3). I3.2 forbinder nu til den rigtige `/ws/zones`, som videresender Async Worker's hændelser i stedet for syntetiske data, og I3.3 gav færre nyheder end 5. oktober, fordi testinstansen starter med et tomt arkiv. Om I1.1 også lykkes fra en telefon, er ikke testet.

## 6.6 Delkonklusion

Integrationstesten viser, at arkitekturens grænseflader fungerer som specificeret: Mobile Client's service-lag, Backend API, Datalaget og de eksterne kilder kan kobles sammen uden tilpasninger, og både UC1 og UC2 kan gennemføres hele vejen igennem. NF4 og NF7 er opfyldt, og NF1 er opfyldt for enkeltforespørgsler. NF1 holder ikke ved 2 forespørgsler i sekundet, og årsagen er den offentlige OSRM-instans, ikke Backend API. Det bekræfter arkitekturbeslutningen om at selvhoste OSRM. Testen gav desuden tre konkrete rettelser: kortere OSRM-timeout, synlig fejl ved geokodning og dubletkontrol på bekræftelser. Alle tre er implementeret og bekræftet i gentesten (afsnit 6.5), sammen med NF10 og NF8; tilbage står kun belastningsdelen af NF1, som kræver den selvhostede OSRM.
