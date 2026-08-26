"""Feature engineering for the segment safety-scoring model.

Turns raw incidents/reports/context for a road segment into the feature
vector the model consumes. See README > Machine Learning Approach.
"""
from dataclasses import dataclass, asdict


@dataclass
class SegmentFeatures:
    recent_incidents_7d: int
    recent_incidents_30d: int
    incident_severity_avg: float  # 0-1, weighted by crime type
    street_lighting: int  # 0 = none, 1 = partial, 2 = well-lit
    pedestrian_density: float  # estimated/modelled foot traffic, 0-1 normalized
    hour_of_day: int  # 0-23
    day_of_week: int  # 0=Mon ... 6=Sun
    community_reports_7d: int
    news_mentions_7d: int

    def to_dict(self) -> dict:
        return asdict(self)


def build_features(segment_id: str, incidents: list[dict], reports: list[dict], context: dict) -> SegmentFeatures:
    """
    NOTE: stub aggregation logic — replace with real windowed queries
    against `incidents`/`reports` filtered to this segment's geometry
    buffer, plus lighting/foot-traffic lookups from `context`.
    """
    return SegmentFeatures(
        recent_incidents_7d=len(incidents),
        recent_incidents_30d=len(incidents) * 3,
        incident_severity_avg=0.4,
        street_lighting=context.get("street_lighting", 1),
        pedestrian_density=context.get("pedestrian_density", 0.5),
        hour_of_day=context.get("hour_of_day", 20),
        day_of_week=context.get("day_of_week", 4),
        community_reports_7d=len(reports),
        news_mentions_7d=context.get("news_mentions_7d", 0),
    )
