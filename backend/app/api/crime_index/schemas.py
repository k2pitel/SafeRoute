"""GET /api/crime-index (F4)."""
from datetime import datetime

from pydantic import BaseModel


class CrimeIndexOut(BaseModel):
    city: str
    crime_index: float
    safety_index: float
    metrics: dict  # e.g. {"level_of_crime": 72.5, "worries_mugging": 65.8, ...}
    ai_summary: str
    contributors: int
    last_updated: datetime
