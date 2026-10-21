"""services.crime_stats (z-score scoring) and services.zones (labels)."""
import pytest

from app.api.zones import crime_stats
from app.api.zones import service as zones
from app.datalag import zone_cache
from tests.factories import municipality, square


def test_average_municipality_scores_midpoint():
    scores = crime_stats.score_from_rates({"a": 300, "b": 400, "c": 500})
    assert scores["b"] == 5.5
    assert scores["a"] > scores["b"] > scores["c"]  # higher crime rate -> lower score


def test_scores_are_clamped_to_1_10():
    rates = {f"m{i}": 400 for i in range(20)} | {"outlier": 100_000}
    scores = crime_stats.score_from_rates(rates)
    assert min(scores.values()) >= 1 and max(scores.values()) <= 10


def test_single_municipality_gets_neutral_score():
    assert crime_stats.score_from_rates({"only": 999}) == {"only": 5.5}


@pytest.mark.parametrize("score,label", [(3.5, "unsafe"), (3.6, "mixed"), (4.3, "mixed"), (4.4, "safe")])
def test_zone_label_cutoffs(score, label):
    assert zones.label_for_score(score) == label


def test_build_stats_skips_aggregate_rows_and_keeps_island_pieces():
    stats = crime_stats.build_municipality_stats(
        crime_by_area={"aarhus": 100, "samsø": 2, "hele landet": 5000},
        population_by_area={"aarhus": 100_000, "samsø": 3_700, "hele landet": 6_000_000},
        boundaries={"aarhus": [square(10.1, 56.1)], "samsø": [square(10.5, 55.8), square(10.6, 55.9)]},
    )
    assert [s.name for s in stats] == ["aarhus", "samsø", "samsø"]
    assert stats[0].crime_rate_per_100k == 100.0


def test_zones_along_finds_each_area_once_in_route_order(monkeypatch):
    multi = {"type": "MultiPolygon", "coordinates": [square(10.5, 56.0)["coordinates"], square(11.0, 56.0)["coordinates"]]}
    monkeypatch.setattr(zone_cache, "_zones", [
        municipality("b", 5.0, multi),
        municipality("a", 5.0, square(10.0, 56.0)),
        municipality("far", 5.0, square(20.0, 50.0)),
    ])
    line = [[10.05, 56.05], [10.06, 56.06], [10.55, 56.05], [11.05, 56.05]]
    assert [z.name for z in zones.zones_along(line)] == ["a", "b"]
