"""GET /api/routes — ranked route options with travel time + tryghedsscore (F1, NF1)."""
from fastapi import APIRouter, Query

from app.api.dependencies import parse_point
from app.api.routes import service as routing
from app.api.routes.schemas import RouteOption

router = APIRouter(prefix="/api/routes", tags=["routes"])


@router.get("", response_model=list[RouteOption])
async def get_routes(
    from_: str = Query(..., alias="from", description="lat,lon"),
    to: str = Query(..., description="lat,lon"),
    mode: str = Query("walking", description="walking | cycling | driving"),
):
    """Candidate routes, fastest first. Always answers, also when OSRM is down (NF7)."""
    return await routing.find_routes(parse_point(from_, "from"), parse_point(to, "to"), mode)
