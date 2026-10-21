"""FastAPI dependencies shared by the routers (dependency injection).

Declared in an endpoint's signature, so a requirement such as "login
required" (F2, UC2 extension 3a) is enforced before the endpoint body runs
and can't be forgotten in a new endpoint. Tests swap implementations via
``app.dependency_overrides``.
"""
from fastapi import Header, HTTPException, Query, Request

from app.api.auth import service as auth
from app.shared.geo import BBox, LatLon
from app.worker import AsyncWorker


def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    """401 unless a valid ``Authorization: Bearer <token>`` header is present."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login required to do that")
    user_id = auth.decode_token(authorization.removeprefix("Bearer "))
    if not user_id:
        raise HTTPException(status_code=401, detail="Session expired — please log in again")
    return user_id


def get_async_worker(request: Request) -> AsyncWorker:
    """The Async Worker instance wired up in main.create_app."""
    return request.app.state.async_worker


def bbox_query(bbox: str = Query(..., description="minLon,minLat,maxLon,maxLat")) -> BBox:
    try:
        return BBox.parse(bbox)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid bbox: {exc}") from exc


def parse_point(raw: str, name: str) -> LatLon:
    try:
        return LatLon.parse(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid '{name}': {exc}") from exc
