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
  getNews: (city) => request(`/api/news${city ? `?city=${encodeURIComponent(city)}` : ""}`),
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
