# 1. Introduktion

Dette kapitel introducerer baggrunden og motivationen for SafeRoute og skitserer det problem, projektet adresserer. Kapitlet beskriver først den samfundsmæssige kontekst, der gør ruteplanlægning med fokus på tryghed relevant (afsnit 1.1), og gennemgår derefter de eksisterende løsninger, folk i dag benytter sig af, samt deres begrænsninger (afsnit 1.2). Herefter præsenteres en overordnet, konceptuel skitse af det foreslåede system (afsnit 1.3), inden kapitlet afsluttes med en problemformulering, der fastlægger projektets omfang og mål (afsnit 1.4).

## 1.1 Baggrund

Hver aften åbner millioner af mennesker en kortapp som Google Maps og får præcis ét svar: den hurtigste vej hjem til fods. Appen tager ikke stilling til, om ruten føles tryg, selvom trygheden for mange spiller lige så stor en rolle som rejsetiden.

Forestil dig en person, der går ud fra en togstation kl. 21.47. Appen siger, at den hurtigste vej hjem er elleve minutter, lige igennem et kvarter uden gadelys og uden andre mennesker, og der findes ikke et andet forslag på skærmen. Personen går ruten alligevel, for alternativet er ikke at vide, hvor man ellers skulle gå hen. Det samme gælder kvinder på vej hjem fra arbejde, turister i en fremmed by, ældre der løber et ærinde efter mørkets frembrud, og forældre der følger et barn hjem: det eneste værktøj, der guider dem gennem byen, har aldrig spurgt, om vejen føles tryg.

Denne utryghed er ikke sjælden, den er normen, både internationalt og i en dansk kontekst. Gallups Global Law and Order-undersøgelse (120+ lande) viser, at 66% af kvinder ikke føler sig trygge ved at gå alene om natten i deres egen by; i Storbritannien fandt Office for National Statistics tilsvarende 38%. Danske tal peger samme vej: Justitsministeriets Tryghedsundersøgelse 2023 finder en signifikant kønsforskel i oplevet utryghed, og Det Kriminalpræventive Råd har opgjort, at cirka hver ottende kvinde, mod hver 20. mand, er bekymret for at gå i sit nærområde efter mørkets frembrud. En DR-artikel fra samme periode beskriver, hvordan det viser sig i konkret adfærd, f.eks. ved at gå med nøgler mellem fingrene eller ringe op med en falsk samtale for at virke mindre sårbar.

Problemet er ikke unikt for storbyer. En Stiften-artikel (2022) beskriver to unge kvinder fra Aarhus, hvor kun den ene tør gå alene hjem om natten. TrygFondens forskningschef peger på, at utrygheden stiger blandt unge (18-24 år) og falder blandt ældre, og Københavns Kommunes Tryghedsundersøgelse 2025 viser tilsvarende, at trygheden varierer markant mellem bydele og aldersgrupper, selvom den samlet set er høj og stigende.

Utrygheden er ikke kun en følelse uden konsekvens. Fodgængere fravælger aktivt ruter, de opfatter som utrygge, uanset rejsetid. Et review af fodgængeres rutevalg (Monash/Cities, 2023) finder, at kvinder systematisk undgår dårligt oplyste ruter om aftenen, uafhængigt af den faktiske kriminalitetsrisiko på stedet: det er den oplevede tryghed, ikke tallene, der styrer adfærden. Konsekvensen er, at folk undgår at gå, betaler for ture de ellers ikke ville tage, eller vælger ruter de ved er dårligere, blot fordi de er velkendte, og det sker i det skjulte, uden at nogen af de værktøjer, folk er afhængige af, registrerer det.

## 1.2 Eksisterende arbejde

De mest udbredte navigationsapps, Google Maps og Apple Maps, optimerer udelukkende for rejsetid og afstand. Et studieprojekt om natlig sikkerhed (Coolight, 2025) bemærker, at disse apps "prioriterer effektivitet over sikkerhed" og i vid udstrækning er designet til bilister, ikke fodgængere. I mangel af et bedre redskab improviserer folk selv: de ringer til en ven og bliver på telefonen hele vejen hjem, deler et "sikre gader"-opslag fra en lokal Facebook-gruppe, spørger en hotelreceptionist, eller gætter ud fra, hvor godt oplyst en gade ser ud i mørket.

Der findes dog en række nichetilbud internationalt, der forsøger at adressere netop dette:

- **SaferRoutes** og **SafeRoute** (iOS-apps) beregner en sikkerhedsscore for gåruter ud fra offentlige kriminalitetsdata, primært i USA, UK og Canada.
- **ZoneScout** og **SafePath** tilbyder lignende funktionalitet: kriminalitetskort og ruter, der undgår "high-risk"-områder, samt en nødknap.
- **Safest Way** (Storbritannien, støttet af Ordnance Survey og UCL) går videre og kombinerer belysningsdata, CCTV-dækning og billedanalyse for at vurdere den oplevede tryghed på en gade, ikke kun den registrerede kriminalitet.
- **SafeWalk AI** (Bryant University, 2026), et studenterprojekt, har som forskningsprototype vist, at maskinlæring på kriminalitetsdata kan bruges til at forudsige risikoniveauer for konkrete gader.

Et nyere studie peger desuden på, at digitale sikkerhedsværktøjers effekt på kønsforskelle i oplevet tryghed fortsat er underbelyst. Kriminalitets-, belysnings- og realtidsdata findes i øvrigt allerede, spredt over kommunale open-data-portaler, OpenStreetMap-tags og lokale nyhedsmedier, men ingen af ovenstående apps samler dem til noget brugbart, før man overhovedet tager det første skridt.

Fælles for de eksisterende løsninger, både de uformelle og de kommercielle, er, at de (a) primært bygger på statiske, historiske data frem for realtidsinput, (b) ikke forklarer, hvorfor en given rute vurderes utryg, og (c) ikke findes for danske byer. Det er den mangel, SafeRoute adresserer.

## 1.3 Systemskitse

Ideen er et navigationssystem til fodgængere, der ud over den hurtigste rute også kan foreslå den tryggeste, og lade brugeren selv vælge, hvad der betyder mest lige nu. Systemet henter information fra offentligt tilgængelige data (f.eks. gadebelysning og historisk kriminalitet) og indrapporteringer fra andre brugere i realtid. Markerer flere brugere en gade som utryg, justerer systemet automatisk sine anbefalinger.

Brugeren møder systemet som en almindelig navigationsapp med et kort, hvor to ruter kan sammenlignes side om side, f.eks. "30 min, utryg" over for "34 min, meget tryg", men kan derudover spørge appen "hvorfor" en rute anbefales, f.eks. "denne gade er dårligt oplyst, og tre brugere har for nylig rapporteret ubehag her". Mens brugeren går, følger appen løbende med og advarer, hvis vedkommende bevæger sig ind i et utrygt område, eller hvis klokken passerer et tidspunkt, hvor utryghed historisk set stiger. For turister og tilflyttere tænkes desuden en søgbar oversigt på by-niveau, der opsummerer, hvor trygt et område generelt opleves.

Systemet er tænkt som en ekstra dimension oven på den navigation, folk allerede kender, ikke en ny app man skal lære fra bunden: tryghed vises synligt og forklaret ved siden af rejsetiden, uden at brugerne skal opgive vanen, de allerede har. Fordi vurderingen opdateres løbende af brugernes egne rapporter, afspejler den, hvad der sker lige nu, og det forudsættes, at de bidragende brugere kan gøre det uden at deres identitet kan spores tilbage til dem.

Formålet med denne skitse er alene at give en intuitiv forståelse af, hvordan systemet hænger sammen konceptuelt; den tekniske realisering fastlægges i senere kapitler. Figur 1.1 illustrerer systemskitsen.

*Figur 1.1: Konceptuel systemskitse (se `systemskitse.puml`).*

## 1.4 Problemformulering/Hypotese

Projektet undersøger, hvordan man kan udvikle et navigationssystem til fodgængere, der, ud over rejsetid, tager hensyn til, hvor trygt en given rute opleves at være. Fodgængere i ukendte eller utrygge gader, herunder i særdeleshed kvinder, turister og ældre, har i dag ikke et samlet redskab til at vurdere, hvilken rute der reelt er tryggest. Det skyldes, at de udbredte navigationsapps udelukkende optimerer for hastighed, og at de få kommercielle alternativer hverken forklarer deres vurderinger eller findes i en dansk kontekst.

Hypotesen er, at det er muligt at kombinere offentligt tilgængelige data (f.eks. belysning og historisk kriminalitet) med brugernes egne realtidsindrapporteringer, så systemet kan:

1. foreslå en rute, der balancerer hastighed og oplevet tryghed efter brugerens eget ønske, og
2. forklare brugeren, hvorfor en given rute eller gade vurderes mere eller mindre tryg.

Antagelsen er, at brugere derved sættes i stand til at træffe mere informerede og trygge valg, uden at skulle opgive den navigationsvane, de allerede har. Projektet afgrænses til en dansk/lokal kontekst (f.eks. Aarhus), hvor en tilsvarende løsning i dag ikke findes, og hvor det derfor er muligt at demonstrere en reel merværdi. Løsningens konkrete tekniske platform ligger uden for denne problemformulering og behandles i de efterfølgende kapitler om krav, design og evaluering.

### Kilder (skal verificeres og formateres til referencelisten)

- Justitsministeriets Forskningskontor, *Tryghedsundersøgelse 2023*
- Det Kriminalpræventive Råd (via Kristeligt Dagblad, 2021)
- DR (2021), "Kvinder har nøgler og hårspray klar..."
- Stiften (2022), "Johanne går ofte alene hjem om natten..."
- Københavns Kommune, *Tryghedsundersøgelsen 2025*
- Gallup, *Global Law and Order*
- UK Office for National Statistics, tryghedstal for kvinder
- "What do pedestrians consider when choosing a route?" (Monash/Cities, 2023)
- "Coolight: Enhancing Nighttime Safety for Urban Student Commuters" (arXiv, 2025)
- "Gender differences in pedestrian safety perceptions" (ScienceDirect, 2025)
- SafeRoute, SaferRoutes, ZoneScout, SafePath, Safest Way, SafeWalk AI (apps/projekter)

---

## A. 30-Second Pitch

Every night, millions of people ask their maps app for the fastest way home. Nobody asks if it's the safest way, because no app has ever offered that as an option. Two out of every three women worldwide say they don't feel safe walking alone at night in their own city, and today's navigation apps do nothing about it. SafeRoute fixes that. We score every street for safety using crime data, lighting, and real-time community reports, then show that score right next to your ETA, so instead of one route, you get a real choice. It's not about fear. It's about finally being asked the question that should have been there all along.

## B. 1-Minute Pitch

It's 9:47 PM. Someone steps off the train, and their maps app tells them the fastest way home is eleven minutes through a street with no lights and nobody else around. There's no second option on the screen, so there's no real choice. They walk it anyway.

That moment happens to millions of people every night. Gallup found that 66% of women worldwide don't feel safe walking alone at night in their own city; the UK's ONS found 38% feel unsafe walking home in their own neighborhood. It's the default experience for a huge share of the people using maps apps every day, and none of the tools they rely on were built with that in mind.

Right now, people patch this themselves: staying on the phone with a friend, guessing which street looks better lit, asking a hotel concierge which way not to walk. That's a workaround for a gap that should never have existed, especially when the data to close it, crime reports, lighting maps, foot traffic, real-time incidents, already exists out there, just scattered and unused.

SafeRoute pulls all of that together. We score every street segment in a city for safety, explain why it's scored that way, and update it in real time as community reports come in. Then we put that score right next to your travel time, so instead of one route, you get an honest choice between four minutes faster and meaningfully safer. Geofenced alerts mean the app stays with you after you start walking, not just while you're planning.

We're not adding fear to your commute. We're adding the one question every navigation app forgot to ask.

## C. Pitch-Deck Version

**Slide 1: The Hook**
Title: "Fastest Isn't Always Safest"
Main message: Every maps app answers one question. It's never the one that matters most after dark.
Bullets:
- Millions of people walk unfamiliar or unsafe streets every night with zero warning
- Today's navigation apps optimize purely for time and distance
- The question "is this safe?" has no place to be asked, let alone answered
Suggested visual: a phone screen showing a single route highlighted on a dark map, no alternative shown.

**Slide 2: The Problem, By the Numbers**
Title: "This Isn't a Niche Problem"
Main message: Feeling unsafe walking alone isn't rare. It's the majority experience.
Bullets:
- 66% of women worldwide don't feel safe walking alone at night in their own city (Gallup, Global Law and Order)
- 38% of women in the UK feel unsafe walking alone in their own neighborhood after dark (UK ONS)
- Tourists, elderly pedestrians, and people with reduced mobility face the same blind spot in every city they enter
Suggested visual: a simple bar chart showing the Gallup and ONS figures side by side.

**Slide 3: Why Nothing Solves This Today**
Title: "The Data Exists. Nobody's Using It."
Main message: Crime data, lighting maps, and real-time reports are all out there, just scattered and disconnected from the app people actually navigate with.
Bullets:
- Google Maps and Apple Maps optimize for time only
- People currently rely on phone calls, guesswork, and secondhand local knowledge
- Open crime data, OSM lighting tags, and news feeds sit unused across dozens of disconnected sources
Suggested visual: scattered data icons (crime report, streetlight, newspaper, phone) with a question mark where they should connect.

**Slide 4: The Solution**
Title: "SafeRoute: Safety as a Routing Parameter"
Main message: We turn scattered safety data into one live score, shown right next to your ETA, for every street in the city.
Bullets:
- Route A, 30 min, risky. Route B, 34 min, very safe. Real choice, not a guess.
- Every score comes with a plain-language reason, not a black box
- Live community reports and geofenced alerts keep the map current and keep you connected after you start walking
Suggested visual: the two-route comparison card (Route A vs Route B) as the centerpiece image.

**Slide 5: Why It Wins**
Title: "Why This, Why Now"
Main message: SafeRoute isn't a replacement for the map you already use, it's the missing second axis.
Bullets:
- Adds safety without asking users to change their habits or switch apps
- Explains every score instead of asking for blind trust
- Updates in real time instead of relying on stale historical data
- Protects contributor privacy through differential privacy, so the community can help without exposure
Suggested visual: simple two-column comparison, "Other Maps" vs "SafeRoute," with a checkmark row for "shows safety."

## D. One-Line Problem Statement

People walking through unfamiliar or unsafe streets, especially women, tourists, and elderly pedestrians, struggle to know which route is actually safe, leading to real fear, avoidable risk, and constant behavioral workarounds, because every major navigation app optimizes purely for speed and has never treated safety as something worth measuring.

## E. One-Line Solution Statement

SafeRoute helps pedestrians choose routes they can actually trust by scoring every street for safety using crime data, lighting, foot traffic, and real-time community reports, and showing that score right next to travel time, unlike Google Maps and Apple Maps, which only ever tell you how fast you'll get there.
