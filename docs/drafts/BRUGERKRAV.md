# 3. Brugerkrav

## 3.1 Introduktion

Dette kapitel beskriver kravene til SafeRoute set fra et brugerperspektiv. Kapitlet indledes med at præsentere systemets kontekst og de aktører, der interagerer med det (afsnit 3.2). Herefter udledes, analyseres og specificeres de funktionelle krav (afsnit 3.3) og de ikke-funktionelle krav (afsnit 3.4). Kapitlet afsluttes med en domænemodel, der beskriver systemet i brugerens termer (afsnit 3.5). Kravene er formuleret, så de er specifikke nok til at kunne danne grundlag for udvikling, men uden at tage stilling til konkret teknologi eller design, medmindre eksterne forhold (f.eks. brug af offentlige datakilder) dikterer dette. Rapporten præsenterer et udvalg af de centrale krav; den fulde liste findes i det separate kravspecifikationsdokument.

## 3.2 Systemkontekst og aktører

SafeRoute opererer i en bymæssig kontekst, hvor fodgængere til daglig skal træffe et rutevalg uden at have et samlet overblik over, hvor trygt de enkelte gader og områder er. Systemet henter derfor data fra kilder uden for sig selv og stiller dem til rådighed for brugeren i en form, der kan bruges i planlægningen af en gåtur.

Følgende aktører er identificeret:

- **Bruger (fodgænger)**: den primære aktør. Søger ruter, vælger mellem hurtigst og tryggest, indrapporterer hændelser, justerer sine indstillinger og deler sin live-position med systemet, mens vedkommende går.
- **Andre brugere (lokalsamfundet)**: samme rolle som Bruger, men set fra perspektivet af de brugere, der bekræfter eller afviser andres indrapporteringer i deres nærområde.
- **Offentlige datakilder** og **Nyhedskilder**: eksterne systemer, der løbende leverer kriminalitets-, belysnings-, kort- og nyhedsdata til SafeRoute, men som ikke selv anvender systemet.
- **Push-notifikationstjeneste**: den eksterne tjeneste (f.eks. Expo/Apple/Google's push-infrastruktur), som SafeRoute sender geofence- og tidsbaserede alarmer igennem, og som leverer dem videre til Brugerens telefon.

Trygsedsscorer og zoner er *ikke* noget en aktør indtaster manuelt. De beregnes automatisk af SafeRoute's AI-model ud fra ovenstående datakilder og brugernes indrapporteringer, og opdateres løbende med tid på døgnet, fordi tryghed ikke er statisk. Der er derfor bevidst ingen "administrator"-aktør i kontekstdiagrammet nedenfor. En eventuel fremtidig mulighed for manuel zonemarkering, f.eks. ved en akut hændelse, der endnu ikke er en del af datagrundlaget, er vurderet lav prioritet og indgår ikke i denne iteration (se F14 i tabel 3.1). Et tidligere udkast inkluderede desuden en "Betroet kontakt"-aktør til nøddeling af position. Den er udeladt her, da den ikke er en del af det nuværende produktomfang.

Figur 3.1 viser aktør-kontekstdiagrammet, herunder hvilken information der udveksles på tværs af systemgrænsen.

*Figur 3.1: Aktør-kontekstdiagram.*

## 3.3 Funktionelle krav

### 3.3.1 Elicitering og analyse

De funktionelle krav udledes ad fire veje. For det første tages der udgangspunkt i problemformuleringen fra kapitel 1: kravene skal samlet sikre, at det system, der skal udvikles, giver en fodgænger et reelt valg mellem en hurtig og en tryg rute, forklaret og løbende opdateret. For det andet konkretiseres kravene gennem brugsscenarier for de målgrupper, projektet retter sig mod: kvinder der går alene om aftenen, ældre, turister i ukendte områder, samt personer med angst eller nedsat mobilitet. Det inkluderer scenariet fra baggrundsafsnittet med en bruger, der går fra togstationen sent om aftenen, samt tilsvarende scenarier for en turist i en ukendt by og en bruger, der observerer en hændelse undervejs. For det tredje holdes kravene op imod de eksisterende løsninger, der er gennemgået i afsnit 1.2 (bl.a. SaferRoutes, ZoneScout, Safest Way), for at sikre, at det planlagte system som minimum skal dække det, brugere allerede forventer af en rute-app, og at de identificerede svagheder ved disse løsninger (statiske data, manglende forklaring, ingen dansk dækning) adresseres som konkrete krav frem for blot som hensigtserklæringer.

For det fjerde tages der udgangspunkt i en indledende produktvision for SafeRoute, som skitserer fem centrale skærmbilleder, systemet skal bestå af: Kort, Rute, Nyheder, Bytryghedsoversigt og Indstillinger, samt den funktionalitet, hvert af dem skal understøtte. Denne vision formaliseres og prioriteres af kravene i dette kapitel. De fem skærmbilleder konkretiseres desuden gennem en række whiteboard-skitser, der skal sikre, at det samlede funktionelle omfang hænger sammen som én brugerrejse, fra en bruger åbner appen, til vedkommende er i gang med at gå en valgt rute.

Analysen giver følgende overordnede funktionelle områder, som de detaljerede krav i afsnit 3.3.2 er struktureret omkring:

1. Finde og sammenligne ruter på tid og tryghed.
2. Forstå, hvorfor en gade eller rute er vurderet, som den er.
3. Indrapportere og verificere hændelser i realtid.
4. Få et hurtigt tryghedsoverblik over en by, man ikke kender.
5. Blive advaret undervejs, i takt med at trygheden ændrer sig i realtid og med tid på døgnet.

### 3.3.2 Specifikation

Den primære aktør, Brugeren, forventes at kunne bruge SafeRoute, som man kender det fra almindelige kortapps: indtast start og destination, se ruteforslag, vælg en rute. Forskellen er, at hvert ruteforslag også bærer en trygsedsscore og en kort forklaring, så valget står mellem tid og tryghed i stedet for kun tid. Da en del af datagrundlaget kommer fra brugerne selv, er det desuden vigtigt, at systemet løbende kan modtage og verificere indrapporteringer, uden at det kan misbruges til at sprede falske alarmer.

**Specifikation**

Kravene med højeste prioritet (Must have) er udfoldet som fuldt udspecificerede use cases nedenfor, da de udgør den funktionalitet, systemet ikke kan fungere uden. De øvrige krav (Should, Could og Won't have) er kortere formuleret direkte i Information-kolonnen i Tabel 3.1, med samme detaljeringsgrad som resten af kravspecifikationsdokumentet, men uden det fulde use case-format, af hensyn til rapportens omfang.

**UC1: Find og vælg tryg rute**

| Felt | Beskrivelse |
|---|---|
| Primær aktør | Bruger (fodgænger) |
| Mål | Brugeren finder og vælger en rute, der afspejler den ønskede balance mellem rejsetid og tryghed. |
| Forudsætninger | Brugeren har åbnet SafeRoute. Enten er lokationstilladelse givet, eller Brugeren er villig til at søge start og destination manuelt. |
| Succeskriterium | En rute er valgt og tegnet på kortet, og Brugeren er klar til at gå. |

Hovedforløb:

1. Brugeren åbner SafeRoute.
2. Brugeren angiver startpunkt, enten ved at bruge sin nuværende position eller ved søgning.
3. Brugeren angiver destination ved søgning.
4. Systemet beregner og viser en liste af ruteforslag, hver med rejsetid og en trygsedsscore fra 1-10, f.eks. "Rute A: 30 min · Tryghed: Middel (6,2/10)".
5. Brugeren sorterer forslagene efter tid eller tryghed (valgfrit).
6. Brugeren vælger ét ruteforslag.
7. Systemet tegner den valgte rute på kortet.
8. Brugeren begynder at gå.

Udvidelser:

- 4a. Der kan ikke beregnes nogen rute (f.eks. ingen sammenhængende gangforbindelse): systemet viser en fejlbesked og beder Brugeren justere start eller destination.
- 2a. Lokationstilladelse er ikke givet: systemet beder om tilladelse eller lader Brugeren søge startpunktet manuelt.

**UC2: Indrapportér hændelse**

| Felt | Beskrivelse |
|---|---|
| Primær aktør | Bruger (fodgænger) |
| Mål | Brugeren advarer andre brugere om en utryg situation nær sin position. |
| Forudsætninger | Brugeren befinder sig i appen med en kendt nuværende position. |
| Succeskriterium | Hændelsen er gemt og vist som ubekræftet på kortet for andre brugere i nærheden. |

Hovedforløb:

1. Brugeren trykker på rapportér-knappen.
2. Systemet henter Brugerens nuværende position.
3. Systemet kontrollerer, om Brugeren er logget ind.
4. Brugeren vælger hændelsestype (chikane, overfald, tyveri, mistænkelig adfærd eller andet) og tidspunkt (nu, 15 min, 30 min eller 1 time siden), og tilføjer eventuelt en kort beskrivelse.
5. Brugeren indsender rapporten.
6. Systemet gemmer rapporten og viser den som ubekræftet på kortet.

Udvidelser:

- 3a. Brugeren er ikke logget ind: systemet beder Brugeren logge ind eller oprette en konto, før rapporten kan indsendes. Afbryder Brugeren login, oprettes rapporten ikke.
- 2a. Lokationstilladelse er ikke givet: systemet beder om tilladelse, før rapporten kan oprettes.

**Tabel 3.1: Funktionelle krav, MoSCoW-prioriteret**

| # | Krav | Prioritet | Information |
|---|---|---|---|
| F1 | Finde og vælge rute sorteret på tid/tryghed | Must have | Brugeren angiver start og destination, hvorefter systemet viser flere ruteforslag med rejsetid og en trygsedsscore fra 1-10, som kan sorteres efter tid eller tryghed. Det valgte forslag tegnes på kortet. Se UC1 for det fulde forløb. |
| F2 | Indrapportere hændelse (kræver login) | Must have | En bruger, der observerer noget utrygt, kan indrapportere det fra sin nuværende position med type, tidspunkt og en valgfri beskrivelse. Kræver login, og rapporten vises som ubekræftet, indtil den er verificeret af andre (jf. F3). Se UC2 for det fulde forløb. |
| F3 | Verificere andres indrapporteringer | Should have | En indrapportering skal bekræftes af flere nærliggende brugere, før den vægtes fuldt i trygsedsscoren. Indtil da vægtes den lavere, for at modvirke spam og fejlagtige rapporter. |
| F4 | Se bytryghedsoversigt for en valgfri by | Should have | Viser en Crime Index og en Safety Index, en række undermålinger, en AI-genereret opsummering samt antal bidragydere og seneste opdatering, for enhver by Brugeren søger. |
| F5 | Realtidsovervågning af gåtur, med geofence- og tidsbaserede push-notifikationer | Should have | Brugerens position følges løbende, mens en rute gås. Der advares både ved indtræden i et utrygt område og på tidspunkter, hvor utryghed historisk set stiger. |
| F6 | Justere risikoprofil og notifikationsindstillinger | Should have | Risikoprofilen (f.eks. hurtigst, balanceret, tryggest) påvirker, hvordan ruteforslag rangeres. Notifikationsindstillinger styrer, hvilke typer advarsler Brugeren modtager. |
| F7 | Se hele kortet farvekodet efter tryghed, uden at have søgt en rute | Should have | Gader og områder er farvekodet efter tryghed direkte på kortets forside, så Brugeren kan danne sig et overblik, selv uden at have søgt en konkret rute. |
| F8 | Se detaljer om en enkelt hændelse ved tryk på dens markør på kortet | Should have | Viser en kort informationsboks med hændelsens type, tidspunkt og en eventuel beskrivelse. |
| F9 | Se kriminalitetsrelateret nyhedsfeed for en by | Could have | Feedet viser kun kriminalitetsrelaterede nyheder for den valgte by og opdateres løbende. |
| F10 | Vælge transportform (gang, cykel eller bil) frem for kun gang | Could have | Systemet er i denne iteration afgrænset til gang, men en transportvælger kunne udvide relevansen til flere brugergrupper. |
| F11 | Se historik over egne tidligere indrapporteringer | Could have | Giver Brugeren mulighed for at følge status på egne rapporter, f.eks. om de er blevet bekræftet af andre. |
| F12 | Dele en valgt rute med andre, f.eks. via et link | Could have | Kan bruges til, at en Bruger lader en anden person følge med i, hvilken rute vedkommende går. |
| F13 | Skifte appens sprog mellem dansk og engelsk | Could have | Relevant for bl.a. turister, der ikke taler dansk. |
| F14 | Manuel override af en AI-beregnet zone, f.eks. ved en akut hændelse, der endnu ikke er en del af datagrundlaget | Won't have (denne iteration) | Ville kræve en administratorrolle og en godkendelsesproces, som ikke indgår i denne iteration. |
| F15 | Understøtte bilnavigation som primær rutetype | Won't have | Systemet er afgrænset til fodgængere, jf. problemformuleringen i kapitel 1. |
| F16 | Fungere fuldt offline uden internetforbindelse | Won't have (denne iteration) | Ville kræve lokal lagring af kort- og scoringsdata og er vurderet for omfattende til denne iteration. |
| F17 | Direkte alarmopkald til 112 fra appen | Won't have | Kræver formelt samarbejde med alarmcentralen og ligger derfor uden for projektets rækkevidde. |

## 3.4 Ikke-funktionelle krav

### 3.4.1 Elicitering og analyse

De ikke-funktionelle krav er udledt af de kvalitetsegenskaber, der er afgørende for, at et system som SafeRoute reelt kan bruges og stoles på: hvor hurtigt det svarer, hvor frisk dataene er, hvor godt det forklarer sig selv, og hvor godt det beskytter de brugere, der bidrager med data.

Et konkret eksempel er kravet til svartid ved rutesøgning. SafeRoute skal kunne bruges i en dansk storby, f.eks. Aarhus midtby en fredag aften, hvor der i myldretiden (kl. 22-24) kan være op til 5.000 samtidige brugere. Antages det, at 2% af disse forespørger en ny rute inden for et givent minut, svarer det til:

```
Nbrugere = 5.000
Forespørgsler/min = 2% × 5.000 = 100
Forespørgsler/sek  = 100 / 60 ≈ 1,7
```

For at ruteforslaget skal føles øjeblikkeligt, ligesom man kender det fra almindelige kortapps, sættes en øvre grænse for svartiden:

```
Trute,maks = 10 sekunder ved op til 2 forespørgsler/sekund
```

Et andet eksempel er kravet til dataens friskhed. Community-indrapporteringer har kun værdi, hvis de når frem til andre brugere, mens de stadig er relevante, typisk inden for den tid, det tager at gå et par gadeblokke. Det giver anledning til et konkret krav om, hvor hurtigt en ny indrapportering skal være synlig for andre.

Tilsvarende er kravet til beskyttelse af bidragydernes privatliv udledt direkte af systemets afhængighed af brugerdreven data: skal brugere kunne stoles på at indrapportere, må det ikke være muligt at genkende dem ud fra de aggregerede data, systemet viser offentligt.

### 3.4.2 Specifikation

Figur 3.2 giver et overblik over de 15 ikke-funktionelle krav, grupperet efter hvilken kvalitetsegenskab de retter sig mod. Tabel 3.2 specificerer dem enkeltvis.

*Figur 3.2: Ikke-funktionelle krav grupperet efter kvalitetsegenskab.*

**Tabel 3.2: Ikke-funktionelle krav, grupperet efter kvalitetsegenskab**

| # | Krav | Kategori | Beskrivelse |
|---|---|---|---|
| NF1 | Performance | Performance | Systemet skal kunne besvare en ruteforespørgsel, inklusive trygsedsscore for alle forslag, inden for 10 sekunder ved op til 2 samtidige forespørgsler pr. sekund. |
| NF2 | Præcision | Performance | Den stedbestemmelse, systemet baserer sig på, skal have en nøjagtighed på maksimalt 10-20 meter i et byområde, da både geofence-advarsler og trygsedsscorer pr. vejsegment mister deres mening, hvis Brugerens position ikke kan bestemmes med rimelig sikkerhed. |
| NF3 | Realtidsovervågning | Performance | Under en aktiv gåtur skal Brugerens position opdateres mindst hvert 15.-30. sekund, eller for hver 25 meter bevægelse, så en geofence-advarsel kan nå frem, mens Brugeren stadig er tæt på det pågældende område, og ikke først efter vedkommende er gået videre. |
| NF4 | Datafriskhed | Pålidelighed | En ny, ubekræftet indrapportering skal være synlig på kortet for andre brugere inden for 1 minut fra indsendelse. |
| NF5 | Pålidelighed | Pålidelighed | En hændelse, der opnår tilstrækkelig verifikation, skal kunne påvirke den viste trygsedsscore for det pågældende område inden for 5 minutter. |
| NF6 | Oppetid | Pålidelighed | Kortfunktionen (visning af ruter og trygsedsscorer) skal have en oppetid på mindst 99,5% målt over en kalendermåned, da systemet er tiltænkt daglig brug. |
| NF7 | Robusthed | Pålidelighed | Er en enkelt ekstern datakilde (f.eks. en nyhedskilde) midlertidigt utilgængelig, skal systemet fortsat kunne vise ruteforslag og trygsedsscorer baseret på de resterende datakilder, frem for at fejle helt. |
| NF8 | Forklarlighed | Brugervenlighed | Enhver vist trygsedsscore skal ledsages af en letforståelig forklaring, baseret på modellens SHAP-værdier, leveret i samme svar som scoren selv, så brugeren ikke oplever mærkbar ekstra ventetid for at få forklaringen. |
| NF9 | Brugervenlighed | Brugervenlighed | En ny bruger skal kunne gennemføre sin første ruteforespørgsel, fra åbning af appen til valgt rute, uden at oprette en konto. Login skal først kræves ved indrapportering af en hændelse. |
| NF10 | Tilgængelighed | Brugervenlighed | Kerneflowet, at finde og vælge en rute, skal kunne gennemføres af en bruger, der benytter en skærmlæser eller anden hjælpeteknologi, så systemet også er brugbart for personer med nedsat syn. |
| NF11 | Privatliv | Sikkerhed og privatliv | Aggregerede positions- og rapportdata, der indgår i offentligt viste trygsedsscorer eller heatmaps, skal anonymiseres via en Laplace-baseret differential privacy-mekanisme med epsilon ≤ 1,0. |
| NF12 | Sikkerhed | Sikkerhed og privatliv | Indrapporteringsfunktionen skal beskyttes mod misbrug og spam, så en enkelt bruger maksimalt kan indsende et fastsat antal rapporter pr. tidsenhed. |
| NF13 | Lovoverholdelse | Sikkerhed og privatliv | Behandling og opbevaring af personoplysninger og lokationsdata skal overholde databeskyttelsesforordningen (GDPR), herunder Brugerens ret til indsigt i og sletning af egne data. |
| NF14 | Kompatibilitet | Kompatibilitet og skalerbarhed | Systemet skal fungere ens for Brugeren, uanset om telefonen kører iOS eller Android, så ingen af de to store brugergrupper udelukkes. |
| NF15 | Skalerbarhed | Kompatibilitet og skalerbarhed | Det skal være muligt at udvide systemet til nye byer, efterhånden som datagrundlaget bliver tilgængeligt, uden at det kræver ændringer i kernefunktionaliteten for de byer, der allerede understøttes. |

## 3.5 Systemets domænemodel

Domænemodellen i figur 3.3 er udledt direkte af kravene i afsnit 3.3 og 3.4 og beskriver de begreber, en bruger møder: en **Bruger** søger **Ruter**, der hver giver flere **Ruteforslag** bestående af **Vejsegmenter** med hver deres trygsedsscore, tidsafhængige bucket (dag/aften/nat) og forklaring. Brugere **indsender** og **verificerer Hændelsesrapporter**, som knytter sig til vejsegmenter. En **By** samler sine vejsegmenter, sit **CrimeIndex**, sine **Nyhedsartikler** og sine **Zoner**, som Brugere kan overvåges imod i realtid (jf. F5) og modtage **Notifikationer** på baggrund af. Modellen forholder sig udelukkende til funktionalitet, data og systemets ydre grænser, ikke til teknologi eller interne grænseflader. Det er genstand for arkitektur- og designkapitlerne.

*Figur 3.3: Domænemodel.*
