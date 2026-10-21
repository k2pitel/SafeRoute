# The Problem SafeRoute Was Built to Solve

## 9:47 PM

She's three blocks from the train station. Google Maps says the fastest way home is eleven minutes, straight through a stretch of road with no streetlights and two boarded-up storefronts. It's also the *only* route the app shows her, because Google Maps has never once asked "is this street safe," only "is this street fast." She takes it anyway. Most people do. There's no alternative on the screen, so there's no alternative in the decision.

That single moment, repeated by hundreds of millions of people every single night in every city on earth, is the entire reason this project exists.

## It isn't a hypothetical. It's the majority experience.

Ask women around the world whether they feel safe walking alone at night in their own city, and most say no. Gallup's Global Law and Order survey, run across more than 120 countries, puts the number at 66%, two out of every three women, in the place they call home, after dark. In the UK, the Office for National Statistics found 38% of women feel unsafe walking alone in their own neighborhood, a place they may have lived in for years and still don't fully trust after sunset. Tourists carry a version of the same problem for a different reason: they're targeted not because a city is uniquely dangerous, but because they simply don't know which turn leads to a well-lit strip and which leads to an empty alley, the kind of knowledge that lives in hushed concierge warnings and forum threads, never in the app that's supposed to be guiding them. Elderly pedestrians, people with anxiety or reduced mobility, parents walking with a kid in tow: they're all quietly running the same calculation every time they step outside. Take the route you know isn't fastest, or take the route the app insists is fastest and hope for the best.

What makes this so frustrating is that the fix isn't a mystery waiting to be invented. The data already exists: crime reports sitting in municipal open-data portals, streetlight tags buried in OpenStreetMap, foot-traffic patterns, local news feeds flagging incidents in real time. It's scattered, but it's there. What's missing isn't information. It's someone willing to fuse it into a signal a person can actually use in the ten seconds before they start walking. Every major navigation app was built to answer one question, how fast, and none of them have ever been built to answer the second one: how does this feel to walk, alone, tonight.

## So we built the app that asks the second question.

SafeRoute treats safety as a first-class routing parameter, not a feature bolted on after the fact. Crime statistics, street lighting, foot-traffic density, live community reports, and local news all feed into a machine-learning model that scores every street segment in a city, and that score rides alongside travel time straight into the routing engine, so instead of one route, you get an honest choice:

> **Route A**: 30 min · 🔴 Safety: risky
> **Route B**: 34 min · 🟢 Safety: very safe

Four minutes. That's the whole trade-off, laid out plainly, instead of buried under a single "fastest route" recommendation that never told you it was making that trade for you in the first place.

From there, the rest of the app follows naturally. The map turns raw incident pins into streets you can read at a glance before you've even left the house, color-coded by what's actually happened there. Every score comes with a SHAP-generated explanation, so instead of a black box telling you a street is "risky," it tells you *why*, elevated because of recent evening incidents nearby, say, which is the difference between a number you tolerate and a number you trust. Community reports let the map react to what's happening right now rather than what happened last year, filtered through differential privacy so contributing to everyone else's safety never means giving up your own. Geofenced alerts and a one-tap panic button mean the app doesn't go quiet once you start walking: it stays with you, and so do the people you'd want to know if something went wrong. And a city-level Crime Index hands travelers and new residents the kind of situational awareness a local only builds after years of living somewhere, instantly, for any city on earth.

None of this comes from a place of fear. It comes from giving people back a choice that's currently being made *for* them, silently, by routing software that was never built with them in mind. SafeRoute doesn't just get you there. It gets you there the way you'd choose to go, if anyone had bothered to ask.
