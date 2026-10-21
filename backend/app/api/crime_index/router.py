"""GET /api/crime-index — bytryghedsoversigt for a city (F4)."""
from fastapi import APIRouter, Query

from app.api.crime_index import service as crime_index
from app.api.crime_index.schemas import CrimeIndexOut

router = APIRouter(prefix="/api/crime-index", tags=["crime-index"])


@router.get("", response_model=CrimeIndexOut)
def get_crime_index(city: str = Query(..., description="City name, e.g. 'Aarhus, Denmark'")):
    return crime_index.get_crime_index(city)
