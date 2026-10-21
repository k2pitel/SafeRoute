"""Bytryghedsoversigt (F4).

NOTE: stub with fixed, representative values so the Mobile Client's Crime
Index screen can be built against the final contract. Swap the body for an
aggregate over ``incidents`` + the AI-summary service.
"""
from datetime import UTC, datetime

from app.api.crime_index.schemas import CrimeIndexOut

_STUB_METRICS = {
    "level_of_crime": 42.5,
    "crime_increasing_5y": 38.1,
    "worries_home_broken": 30.2,
    "worries_mugged": 27.9,
    "worries_car_stolen": 25.4,
    "problem_drugs": 35.0,
    "problem_property_crime": 33.8,
    "problem_violent_crime": 21.6,
    "safety_walking_daylight": 78.4,
    "safety_walking_night": 55.2,
}


def get_crime_index(city: str) -> CrimeIndexOut:
    ai_summary = (
        f"{city} generally reports low-to-moderate crime levels, with daytime "
        "walking rated as safe by most contributors. Night-time safety drops "
        "moderately in a few areas — consider a well-lit route after dark and "
        "check the map for any recently reported incidents nearby."
    )
    return CrimeIndexOut(
        city=city,
        crime_index=34.7,
        safety_index=65.3,
        metrics=dict(_STUB_METRICS),
        ai_summary=ai_summary,
        contributors=128,
        last_updated=datetime.now(UTC),
    )
