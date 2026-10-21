// Ranking of route options (UC1 step 5, F6). Pure, so it's unit-tested.

export const SORT_OPTIONS = [
  { value: "time", label: "Fastest" },
  { value: "balanced", label: "Balanced" },
  { value: "safety", label: "Safest" },
];

// F6: the risk profile picks the default ranking; the user can still re-sort.
const SORT_FOR_PROFILE = { fast: "time", balanced: "balanced", safest: "safety" };

export function sortForProfile(riskProfile) {
  return SORT_FOR_PROFILE[riskProfile] || "balanced";
}

// Balanced: safety score minus one point per 10 % extra walking time
// compared to the fastest option — e.g. a route that is 20 % slower must be
// at least 2 points safer to rank above the fastest one.
const POINTS_PER_EXTRA_TIME = 10;

function balancedScore(route, fastestMinutes) {
  const extraTime = fastestMinutes > 0 ? route.duration_minutes / fastestMinutes - 1 : 0;
  return route.safety_score - POINTS_PER_EXTRA_TIME * extraTime;
}

export function rankRoutes(routes, sortBy) {
  const fastest = Math.min(...routes.map((r) => r.duration_minutes));
  const key = {
    time: (r) => r.duration_minutes,
    safety: (r) => -r.safety_score,
    balanced: (r) => -balancedScore(r, fastest),
  }[sortBy];
  return [...routes].sort((a, b) => key(a) - key(b));
}
