"""Pydantic request/response schemas."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class IncidentOut(BaseModel):
    id: int
    type: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    occurred_at: datetime
    source: str
    verified: bool

    class Config:
        from_attributes = True


class RouteOption(BaseModel):
    """A single candidate route returned by /api/routes."""

    duration_minutes: float
    distance_meters: float
    safety_score: float = Field(..., ge=1, le=10, description="1 = least safe, 10 = safest")
    safety_label: str  # e.g. 'not safe' | 'okay' | 'safe' | 'very safe'
    geometry: dict  # GeoJSON LineString


class ReportCreate(BaseModel):
    user_id: uuid.UUID
    latitude: float
    longitude: float
    description: Optional[str] = None


class ReportOut(BaseModel):
    id: int
    latitude: float
    longitude: float
    description: Optional[str] = None
    confirmations: int
    created_at: datetime

    class Config:
        from_attributes = True


class ZoneOut(BaseModel):
    """A clustered danger/uncertain area — README > Home/Map Page 'Bad Zone'."""

    id: str
    safety_score: float = Field(..., ge=1, le=10)
    safety_label: str  # 'unsafe' | 'mixed' | 'safe'
    geometry: dict  # GeoJSON Polygon


class SegmentExplanation(BaseModel):
    segment_id: str
    safety_score: float
    top_features: list[dict]  # e.g. [{"feature": "recent_incidents_7d", "impact": 0.42}, ...]


class CrimeIndexOut(BaseModel):
    city: str
    crime_index: float
    safety_index: float
    metrics: dict  # e.g. {"level_of_crime": 72.5, "worries_mugging": 65.8, ...}
    ai_summary: str
    contributors: int
    last_updated: datetime


class NewsItem(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime
    summary: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
