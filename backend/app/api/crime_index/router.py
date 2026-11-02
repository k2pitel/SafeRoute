"""GET /api/crime-index — bytryghedsoversigt for a city (F4)."""
from fastapi import APIRouter, HTTPException, Query

from app.api.crime_index import service as crime_index
from app.api.crime_index import world
from app.api.crime_index.schemas import CitySafetyOut, CountrySafetyOut, CrimeIndexOut, WorldSafetySources

router = APIRouter(prefix="/api/crime-index", tags=["crime-index"])


@router.get("", response_model=CrimeIndexOut)
def get_crime_index(city: str = Query(..., description="City or municipality, e.g. 'Aarhus' or 'Aarhus, Denmark'")):
    try:
        return crime_index.get_crime_index(city)
    except crime_index.DataNotLoadedError:
        raise HTTPException(status_code=503, detail="Crime statistics are still loading — try again in a minute")
    except crime_index.CityNotFoundError:
        raise HTTPException(status_code=404, detail=f"No data for '{city}'. Only Danish cities are covered so far.")


@router.get("/cities", response_model=list[str])
def list_cities():
    """Municipalities with data, for the city picker (US-29)."""
    return crime_index.list_cities()


def _require_world_data() -> None:
    if not world.loaded():
        raise HTTPException(status_code=503, detail="Country data is still loading - try again in a minute")


@router.get("/countries", response_model=list[CountrySafetyOut])
def country_ranking(region: str | None = Query(None, description="Filter, e.g. 'Europe & Central Asia'")):
    """Country ranking by Crime Index (rank 1 = most crime). Free official data:
    World Bank homicide rates + Eurostat crime-in-area survey."""
    _require_world_data()
    rows = world.country_ranking()
    if region:
        rows = [r for r in rows if r["region"].lower() == region.lower()]
    return rows


@router.get("/world-cities", response_model=list[CitySafetyOut])
def city_ranking():
    """European cities by share of residents who feel safe walking alone at
    night (Eurostat perception survey). Rank 1 = safest."""
    _require_world_data()
    return world.city_ranking()


@router.get("/sources", response_model=WorldSafetySources)
def sources():
    """Attribution lines the app shows next to these numbers."""
    return world.SOURCES
