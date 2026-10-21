// Thin API client for the SafeRoute backend.
// Base URL is read from app config / env — see mobile/.env.example.
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000";

// Set by AuthContext once a user logs in/out, so every request can carry
// the session token without every call site having to pass it explicitly.
let authToken = null;
export function setAuthToken(token) {
  authToken = token;
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    // Prefer FastAPI's {"detail": ...} message over a generic status-code
    // error where available. `detail` is usually a plain string (e.g.
    // "Invalid email or password"), but on a 422 validation error it's a
    // list of {msg, loc, ...} objects instead — join those into readable
    // text rather than letting them stringify to "[object Object]".
    let message = `API error ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body?.detail)) {
        message = body.detail.map((issue) => issue.msg || JSON.stringify(issue)).join("; ");
      }
    } catch {
      // non-JSON error body — fall back to the generic message above
    }
    throw new Error(message);
  }
  return res.json();
}

export const api = {
  getIncidents: (bbox) => request(`/api/incidents?bbox=${bbox}`),
  getZones: (bbox) => request(`/api/zones?bbox=${bbox}`),
  getRoutes: (from, to, mode = "walking") =>
    request(`/api/routes?from=${from}&to=${to}&mode=${mode}`),
  getReports: (bbox) => request(`/api/reports?bbox=${bbox}`),
  submitReport: (report) =>
    request("/api/reports", { method: "POST", body: JSON.stringify(report) }),
  confirmReport: (id) => request(`/api/reports/${id}/confirm`, { method: "POST" }),
  signup: (email, password) =>
    request("/api/auth/signup", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email, password) =>
    request("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
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
  // this year's news — see backend/app/api/news/router.py's get_news docstring.
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
