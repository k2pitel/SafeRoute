"""services.routing: score -> label thresholds and the NF8 explanation."""
import pytest

from app.api.routes import service as routing
from app.datalag import zone_cache
from tests.factories import municipality, square


@pytest.mark.parametrize(
    "score,label",
    [(1, "not safe"), (3.99, "not safe"), (4, "okay"), (6, "safe"), (8, "very safe"), (10, "very safe")],
)
def test_label_thresholds(score, label):
    assert routing.label_for_score(score) == label


def test_explanation_names_areas_passed_with_real_rate(monkeypatch):
    aarhus = municipality("aarhus", 3.2, square(10.1, 56.1))
    aarhus.crime_rate_per_100k = 612.5
    monkeypatch.setattr(zone_cache, "_zones", [aarhus, municipality("odense", 6.0, square(10.3, 55.3))])
    line = {"type": "LineString", "coordinates": [[10.15, 56.15], [10.18, 56.16]]}

    text = routing.explain(line)
    assert "Aarhus: 612.5 violent crimes per 100,000/yr (well above the national average)" in text
    assert "Odense" not in text
    assert "not scored yet" in text  # honest about what the score doesn't cover


def test_explanation_without_zone_data(monkeypatch):
    monkeypatch.setattr(zone_cache, "_zones", [])
    text = routing.explain({"type": "LineString", "coordinates": [[10.15, 56.15]]}, estimated=True)
    assert text.startswith("Route engine unavailable")
    assert "No area crime data" in text
