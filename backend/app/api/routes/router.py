"""GET /api/routes — ranked route options with travel time + tryghedsscore (F1, NF1)."""
from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import parse_point
from app.api.routes import service as routing
from app.api.routes.schemas import RouteOption

router = APIRouter(prefix="/api/routes", tags=["routes"])


@router.get("", response_model=list[RouteOption])
async def get_routes(
    from_: str = Query(..., alias="from", description="lat,lon"),
    to: str = Query(..., description="lat,lon"),
    mode: str = Query("walking", description="walking | cycling (US-37); driving is out of scope (F15)"),
):
    """Candidate routes, fastest first. Always answers, also when OSRM is down (NF7)."""
    try:
        return await routing.find_routes(parse_point(from_, "from"), parse_point(to, "to"), mode)
    except routing.UnsupportedModeError:
        raise HTTPException(status_code=422, detail="mode must be 'walking' or 'cycling'")
