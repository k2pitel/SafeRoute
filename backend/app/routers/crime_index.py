"""GET /api/crime-index — city-level crime/safety index + AI summary."""
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from app.schemas import CrimeIndexOut

router = APIRouter(prefix="/api/crime-index", tags=["crime-index"])


@router.get("", response_model=CrimeIndexOut)
def get_crime_index(city: str = Query(..., description="City name, e.g. 'Aarhus, Denmark'")):
    """
    NOTE: stub with representative mock values (mirrors the Numbeo-style
    layout in README > Crime Index Page). Swap for a query against
    aggregated `incidents` + a call to the AI-summary service.
    """
    metrics = {
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
        metrics=metrics,
        ai_summary=ai_summary,
        contributors=128,
        last_updated=datetime.now(timezone.utc),
    )
