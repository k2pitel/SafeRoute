"""Rule-based baseline tryghedsscore (ML-03).

A transparent formula used until a trained model exists (and as the
fallback whenever none is loaded). It has the same shape as
``serving.SafetyScorer.score``: ``(score, contributions)``, so callers
don't care which scorer they get.

    score = zone_base − report_penalty − time_penalty, clamped to 1–10

- zone_base: mean tryghedsscore of the municipalities the route passes
  (official violent-crime rate, api/zones/crime_stats.py); 5.5 = national
  average when no zone data is loaded.
- report_penalty: community reports within REPORT_RADIUS_M of the route,
  weighted by verification (F3) and age (half-life REPORT_HALF_LIFE_HOURS),
  with Laplace noise on the weighted count (NF11, worker/scoring/laplace.py).
- time_penalty: evening and night, when unsafety historically rises (F5).

Street lighting and foot traffic (DP-06) aren't available yet, so they are
listed as "not scored" rather than guessed. The weights are a starting
point to be justified in ch.5 and replaced by the trained model (ML-04).
"""
import hashlib
from dataclasses import dataclass

import numpy as np

NATIONAL_AVERAGE_SCORE = 5.5
REPORT_RADIUS_M = 100
REPORT_HALF_LIFE_HOURS = 7 * 24
VERIFIED_WEIGHT = 1.0
UNVERIFIED_WEIGHT = 0.3
PENALTY_PER_REPORT = 0.7
MAX_REPORT_PENALTY = 3.0
NIGHT_HOURS = range(5)  # 00–05
EVENING_HOURS = (*range(18, 24), 5)  # 18–24 and the 05 hour
NIGHT_PENALTY = 0.8
EVENING_PENALTY = 0.4


@dataclass
class NearbyReport:
    id: int
    verified: bool
    age_hours: float


def report_weight(report: NearbyReport) -> float:
    base = VERIFIED_WEIGHT if report.verified else UNVERIFIED_WEIGHT
    return base * 0.5 ** (max(report.age_hours, 0) / REPORT_HALF_LIFE_HOURS)


def _noisy(value: float, report_ids: list[int], epsilon: float) -> float:
    """Laplace noise (sensitivity 1: one person adds at most one report),
    seeded by the set of reports involved. The same reports always get the
    same noise, so asking repeatedly and averaging reveals nothing more —
    the averaging attack afsnit 4.2.4 warns about for per-read noise."""
    if not report_ids or epsilon <= 0:
        return value
    seed = int(hashlib.sha256(",".join(map(str, sorted(report_ids))).encode()).hexdigest()[:8], 16)
    noise = np.random.default_rng(seed).laplace(0.0, 1.0 / epsilon)
    return max(0.0, value + float(noise))


def score_route(
    zone_scores: list[float],
    reports: list[NearbyReport],
    hour: int,
    epsilon: float = 1.0,
) -> tuple[float, list[dict]]:
    """Returns (score 1–10, contributions sorted by |impact|). Each
    contribution: {"factor", "impact", "detail"}; impact is in score points."""
    contributions: list[dict] = []

    if zone_scores:
        base = sum(zone_scores) / len(zone_scores)
        contributions.append({
            "factor": "area_crime",
            "impact": round(base - NATIONAL_AVERAGE_SCORE, 2),
            "detail": f"official crime rate of the {len(zone_scores)} area(s) passed",
        })
    else:
        base = NATIONAL_AVERAGE_SCORE
        contributions.append({"factor": "area_crime", "impact": 0.0, "detail": "no area data loaded"})

    weighted = sum(report_weight(r) for r in reports)
    noisy = _noisy(weighted, [r.id for r in reports], epsilon)
    report_penalty = min(MAX_REPORT_PENALTY, PENALTY_PER_REPORT * noisy)
    verified = sum(1 for r in reports if r.verified)
    contributions.append({
        "factor": "recent_reports",
        "impact": -round(report_penalty, 2),
        "detail": (
            f"{len(reports)} community report(s) within {REPORT_RADIUS_M} m ({verified} verified)"
            if reports else f"no community reports within {REPORT_RADIUS_M} m"
        ),
    })

    if hour in NIGHT_HOURS:
        time_penalty, when = NIGHT_PENALTY, "night"
    elif hour in EVENING_HOURS:
        time_penalty, when = EVENING_PENALTY, "evening"
    else:
        time_penalty, when = 0.0, "daytime"
    contributions.append({"factor": "time_of_day", "impact": -time_penalty, "detail": when})

    score = round(min(10.0, max(1.0, base - report_penalty - time_penalty)), 1)
    contributions.sort(key=lambda c: abs(c["impact"]), reverse=True)
    return score, contributions
