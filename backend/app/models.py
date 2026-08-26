"""SQLAlchemy ORM models — mirrors the schema described in the README."""
import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Incident(Base):
    """A single crime/safety incident, from official data, news, or the community."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    description = Column(Text)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(50), nullable=False)  # 'official' | 'community' | 'news'
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class SegmentScore(Base):
    """Precomputed safety score for a road segment at a given time bucket."""

    __tablename__ = "segment_scores"

    id = Column(Integer, primary_key=True)
    segment_id = Column(String(64), nullable=False, index=True)  # OSRM/OSM way id
    geom = Column(Geography(geometry_type="LINESTRING", srid=4326), nullable=False)
    safety_score = Column(Numeric(4, 2), nullable=False)  # 1.00–10.00
    time_bucket = Column(String(20), nullable=False)  # 'day' | 'evening' | 'night'
    shap_summary = Column(JSONB)  # top contributing features, for explainability
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Report(Base):
    """A community-submitted, real-time safety report."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    description = Column(Text)
    confirmations = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="reports")


class User(Base):
    """App user / risk profile / emergency contacts."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_profile = Column(String(20), default="balanced")  # 'fast' | 'balanced' | 'safest'
    emergency_contacts = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    reports = relationship("Report", back_populates="user")
