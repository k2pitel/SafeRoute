import Constants from "expo-constants";

// Thin API client for the SafeRoute backend.
// EXPO_PUBLIC_API_BASE_URL wins when set (see mobile/.env.example). Otherwise,
// in development, the phone already reaches Metro at <host>:8081, so the
// backend is assumed on the same host at :8000 — no LAN IP to keep in sync.
function devServerApiUrl() {
  const host = Constants.expoConfig?.hostUri?.split(":")[0];
  return host ? `http://${host}:8000` : null;
}

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL || devServerApiUrl() || "http://localhost:8000";

const REQUEST_TIMEOUT_MS = 30000;

// Set by AuthContext once a user logs in/out, so every request can carry
// the session token without every call site having to pass it explicitly.
let authToken = null;
export function setAuthToken(token) {
  authToken = token;
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  // A dead tunnel can leave fetch hanging instead of failing; give up after
  // REQUEST_TIMEOUT_MS so screens show "can't reach" rather than spin forever.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let res;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers, signal: controller.signal });
  } catch {
    // The server never answered (dead tunnel, wrong LAN IP, backend not
    // running). Say so, instead of letting callers report it as e.g.
    // "no route found". `offline` lets them tell the two cases apart.
    const error = new Error(`Can't reach the SafeRoute server at ${API_BASE_URL}`);
    error.offline = true;
    throw error;
  } finally {
    clearTimeout(timer);
  }
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
  if (res.status === 204) return null; // e.g. DELETE /api/auth/me
  return res.json();
}

export const api = {
  getIncidents: (bbox) => request(`/api/incidents?bbox=${bbox}`),
  getZones: (bbox) => request(`/api/zones?bbox=${bbox}`),
  getRoutes: (from, to, mode = "walking") =>
    request(`/api/routes?from=${from}&to=${to}&mode=${mode}`),
  // US-38 / US-59: the signed-in user's own data.
  getMyReports: () => request("/api/auth/me/reports"),
  exportMyData: () => request("/api/auth/me/export"),
  deleteAccount: () => request("/api/auth/me", { method: "DELETE" }),
  // US-29 / DP-07
  getCrimeIndexCities: () => request("/api/crime-index/cities"),
  // Free stand-ins for a paid crime index: Eurostat + World Bank.
  getCountryRanking: () => request("/api/crime-index/countries"),
  getEuropeanCityRanking: () => request("/api/crime-index/world-cities"),
  getPipelineStatus: () => request("/api/pipeline/status"),
  getReports: (bbox) => request(`/api/reports?bbox=${bbox}`),
  submitReport: (report) =>
    request("/api/reports", { method: "POST", body: JSON.stringify(report) }),
  confirmReport: (id) => request(`/api/reports/${id}/confirm`, { method: "POST" }),
  signup: (email, password) =>
    request("/api/auth/signup", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email, password) =>
    request("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  getCrimeIndex: (city) => request(`/api/crime-index?city=${encodeURIComponent(city)}`),
  // period: { from, to } years → that range from the archive; otherwise
  // latest (live feeds + newest archive), or one `year`.
  getNews: (city, year, period) => {
    const params = new URLSearchParams();
    if (city) params.set("city", city);
    if (period) {
      params.set("from", String(period.from));
      params.set("to", String(period.to));
    } else if (year) {
      params.set("year", String(year));
    }
    const qs = params.toString();
    return request(`/api/news${qs ? `?${qs}` : ""}`);
  },
  // Map pins: only articles placed on the map, for a year range (one request,
  // instead of one per year as before).
  getNewsPins: (period) => request(`/api/news?from=${period.from}&to=${period.to}&located=true`),
  getNewsYears: () => request("/api/news/years"),
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
