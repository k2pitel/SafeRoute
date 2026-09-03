// Thin API client for the SafeRoute backend.
// Base URL is read from app config / env — see mobile/.env.example.
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

export const api = {
  getIncidents: (bbox) => request(`/api/incidents?bbox=${bbox}`),
  getZones: (bbox) => request(`/api/zones?bbox=${bbox}`),
  getRoutes: (from, to, mode = "walking") =>
    request(`/api/routes?from=${from}&to=${to}&mode=${mode}`),
  submitReport: (report) =>
    request("/api/reports", { method: "POST", body: JSON.stringify(report) }),
  confirmReport: (id) => request(`/api/reports/${id}/confirm`, { method: "POST" }),
  getCrimeIndex: (city) => request(`/api/crime-index?city=${encodeURIComponent(city)}`),
  getNews: (city, year) => {
    const params = new URLSearchParams();
    if (city) params.set("city", city);
    if (year) params.set("year", String(year));
    const qs = params.toString();
    return request(`/api/news${qs ? `?${qs}` : ""}`);
  },
  // Latest-only (no `year`) merges live feeds with just the most-recently
  // archived items, so with years of archive built up it's almost entirely
  // this year's news — see backend/app/routers/news.py's get_news docstring.
  // Map pins should reflect the whole archive, so this pulls every year on
  // top of "latest" and merges, deduping by URL.
  getNewsAllYears: async (startYear = 2020) => {
    const currentYear = new Date().getFullYear();
    const years = [];
    for (let y = startYear; y <= currentYear; y++) years.push(y);

    const batches = await Promise.all([
      api.getNews(),
      ...years.map((y) => api.getNews(undefined, y).catch(() => [])),
    ]);

    const seen = new Set();
    const merged = [];
    for (const batch of batches) {
      for (const item of batch) {
        const key = item.url || item.title;
        if (seen.has(key)) continue;
        seen.add(key);
        merged.push(item);
      }
    }
    return merged;
  },
  explainSegment: (segmentId) => request(`/api/segments/${segmentId}/explain`),
};

// Opens a live WebSocket connection for zone/score updates.
// Usage: const ws = openZonesFeed((update) => { ... });
export function openZonesFeed(onMessage) {
  const wsUrl = API_BASE_URL.replace(/^http/, "ws");
  const socket = new WebSocket(`${wsUrl}/ws/zones`);
  socket.onmessage = (event) => onMessage(JSON.parse(event.data));
  return socket;
}
