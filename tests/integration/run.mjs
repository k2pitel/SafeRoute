// Integration test driver (kapitel 6): drives the Mobile Client's real
// service layer (mobile/src/services/api.js + geocoding.js, unchanged)
// against running Backend API instances. No mocks: the backend calls the
// real OSRM, Danmarks Statistik, RSS feeds and its Datalag.
//
// Start the backends first (backend venv Python, from the repo root):
//   python tests/integration/serve.py --port 8001                                # normal
//   python tests/integration/serve.py --port 8002 --osrm-url http://127.0.0.1:9  # OSRM refuses (NF7)
//   python tests/integration/serve.py --port 8003 --osrm-url http://127.0.0.1:5999  # OSRM hangs (I1.7, optional)
// then:
//   node tests/integration/run.mjs            # functional tests
//   node tests/integration/run.mjs --load     # + NF1 load tests (I1.5/I1.6) — hits the public OSRM hard
//
// Each "phone" is a separate module instance of api.js with its own base
// URL and login token, like separate devices.
import { copyFileSync } from "node:fs";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SERVICES = path.resolve(HERE, "../../mobile/src/services");
const URL_A = process.env.IT_BACKEND_URL ?? "http://127.0.0.1:8001";
const URL_OSRM_DOWN = process.env.IT_BACKEND_OSRM_DOWN_URL ?? "http://127.0.0.1:8002";
const URL_OSRM_HANGS = process.env.IT_BACKEND_OSRM_HANGS_URL ?? "http://127.0.0.1:8003";
const HANGING_OSRM_PORT = 5999;
const RUN_LOAD = process.argv.includes("--load");

const AARHUS_H = { latitude: 56.1504, longitude: 10.2045 };
const UNIVERSITETSPARKEN = { latitude: 56.1681, longitude: 10.203 };
const AARHUS_BBOX = "10.1,56.1,10.3,56.2";
const point = (p) => `${p.latitude},${p.longitude}`;

// The services are ES modules written for Metro (.js, no "type": "module"):
// copy them to .mjs (git-ignored) so Node loads them as-is.
for (const name of ["api", "geocoding"]) {
  copyFileSync(path.join(SERVICES, `${name}.js`), path.join(HERE, `${name}.mjs`));
}

async function phone(name, baseUrl) {
  process.env.EXPO_PUBLIC_API_BASE_URL = baseUrl; // read by api.js at module load
  return import(`./api.mjs?phone=${name}`);
}

const results = [];
async function check(table, id, iface, title, fn) {
  const started = performance.now();
  try {
    const detail = await fn();
    results.push({ table, id, iface, title, ok: true, detail, ms: performance.now() - started });
  } catch (e) {
    results.push({ table, id, iface, title, ok: false, detail: e.message, ms: performance.now() - started });
  }
}
function expect(condition, message) {
  if (!condition) throw new Error(message);
}
async function rejects(promise, pattern) {
  try {
    await promise;
  } catch (e) {
    expect(pattern.test(e.message), `wrong error: "${e.message}"`);
    return `rejected: "${e.message}"`;
  }
  throw new Error("was accepted");
}
async function reachable(baseUrl) {
  try {
    return (await fetch(`${baseUrl}/health`)).ok;
  } catch {
    return false;
  }
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const unique = () => `it-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;

// ---------------------------------------------------------------------------
if (!(await reachable(URL_A))) {
  console.error(`Backend API not reachable at ${URL_A} — start tests/integration/serve.py first.`);
  process.exit(2);
}
const A = await phone("A", URL_A);
const B = await phone("B", URL_A);
const { searchPlaces } = await import("./geocoding.mjs");

// --- UC1: Find og vælg tryg rute ---
await check("UC1", "I1.1", "Mobile → Nominatim", 'searchPlaces("Aarhus H")', async () => {
  const places = await searchPlaces("Aarhus H");
  expect(places.length > 0, "no places");
  return `${places.length} places, first: ${places[0].primary}, ${places[0].secondary}`;
});

let routes = [];
await check("UC1", "I1.2", "Mobile → Backend → OSRM", "getRoutes Aarhus H → Universitetsparken", async () => {
  routes = await A.api.getRoutes(point(AARHUS_H), point(UNIVERSITETSPARKEN));
  expect(routes.length > 0, "no routes");
  expect(!routes[0].explanation.startsWith("Route engine unavailable"), "got the NF7 fallback, OSRM not used");
  return routes
    .map((r) => `${r.duration_minutes.toFixed(1)} min/${Math.round(r.distance_meters)} m (${r.geometry.coordinates.length} coords)`)
    .join("; ");
});

await check("UC1", "I1.3", "Backend → Mobile", "RouteOption contract incl. NF8 explanation", async () => {
  expect(routes.length > 0, "no routes from I1.2");
  const labels = ["not safe", "okay", "safe", "very safe"];
  for (const r of routes) {
    expect(r.safety_score >= 1 && r.safety_score <= 10, `score ${r.safety_score}`);
    expect(labels.includes(r.safety_label), `label ${r.safety_label}`);
    expect(r.explanation?.length > 0, "missing explanation (NF8)");
  }
  const durations = routes.map((r) => r.duration_minutes);
  expect(durations.every((d, i) => i === 0 || durations[i - 1] <= d), "not fastest first");
  const [lon, lat] = routes[0].geometry.coordinates[0];
  expect(Math.abs(lat - AARHUS_H.latitude) < 0.01 && Math.abs(lon - AARHUS_H.longitude) < 0.01, "GeoJSON not [lon, lat] at start");
  return `explanation: "${routes[0].explanation}"`;
});

if (await reachable(URL_OSRM_DOWN)) {
  const C = await phone("C", URL_OSRM_DOWN);
  await check("UC1", "I1.4", "Backend → OSRM (refused)", "Fallback, NF7", async () => {
    const fallback = await C.api.getRoutes(point(AARHUS_H), point(UNIVERSITETSPARKEN));
    expect(fallback.length === 2, `${fallback.length} options`);
    expect(fallback.every((r) => r.explanation.startsWith("Route engine unavailable")), "not marked as estimate");
    return "200 with 2 straight-line options, marked as estimates";
  });
} else {
  results.push({ table: "UC1", id: "I1.4", iface: "Backend → OSRM (refused)", title: "Fallback, NF7", ok: false, detail: `skipped: nothing on ${URL_OSRM_DOWN}` });
}

if (await reachable(URL_OSRM_HANGS)) {
  // An "OSRM" that accepts connections and never answers.
  const hanging = net.createServer(() => {}).listen(HANGING_OSRM_PORT, "127.0.0.1");
  const D = await phone("D", URL_OSRM_HANGS);
  await check("UC1", "I1.7", "Backend → OSRM (hangs)", "Time until fallback, NF1 budget 10 s", async () => {
    const t0 = performance.now();
    const fallback = await D.api.getRoutes(point(AARHUS_H), point(UNIVERSITETSPARKEN));
    const seconds = (performance.now() - t0) / 1000;
    expect(fallback.length === 2, "no fallback");
    expect(seconds < 10, `${seconds.toFixed(1)} s`);
    return `fallback after ${seconds.toFixed(1)} s`;
  });
  hanging.close();
}

if (RUN_LOAD) {
  await check("UC1", "I1.5", "Mobile → Backend → OSRM", "NF1: 20 sequential requests", async () => {
    const times = [];
    for (let i = 0; i < 20; i++) {
      const t0 = performance.now();
      await A.api.getRoutes(point(AARHUS_H), point(UNIVERSITETSPARKEN));
      times.push(performance.now() - t0);
    }
    times.sort((x, y) => x - y);
    expect(times[19] < 10_000, `max ${Math.round(times[19])} ms`);
    return `median ${Math.round(times[10])} ms, max ${Math.round(times[19])} ms`;
  });
  await check("UC1", "I1.6", "Mobile → Backend → OSRM", "NF1: 2 req/s for 15 s", async () => {
    const pending = [];
    for (let i = 0; i < 30; i++) {
      const t0 = performance.now();
      pending.push(A.api.getRoutes(point(AARHUS_H), point(UNIVERSITETSPARKEN)).then(() => performance.now() - t0));
      await sleep(500);
    }
    const times = (await Promise.all(pending)).sort((x, y) => x - y);
    const over = times.filter((t) => t > 10_000).length;
    expect(over === 0, `${over} of 30 over 10 s (median ${(times[15] / 1000).toFixed(1)} s)`);
    return `median ${Math.round(times[15])} ms, max ${Math.round(times[29])} ms`;
  });
}

// --- UC2: Indrapportér hændelse ---
const report = { type: "harassment", latitude: 56.157, longitude: 10.21, description: "Integrationstest" };
let created;

await check("UC2", "I2.1", "Mobile → Backend", "submitReport without login (extension 3a)", () =>
  rejects(A.api.submitReport(report), /Login required/)
);

const emailA = unique();
await check("UC2", "I2.2", "Mobile → Backend → Datalag", "signup → setAuthToken → submitReport", async () => {
  const { access_token } = await A.api.signup(emailA, "hemmeligt");
  A.setAuthToken(access_token);
  created = await A.api.submitReport(report);
  expect(created.confirmations === 0, `confirmations ${created.confirmations}`);
  expect(!("user_id" in created), "user_id exposed");
  return `201, id ${created.id}, confirmations 0, no user_id`;
});

await check("UC2", "I2.3", "Datalag → Backend → other phone", "NF4: report visible to another client without login", async () => {
  const t0 = performance.now();
  const seen = (await B.api.getReports(AARHUS_BBOX)).find((r) => r.id === created?.id);
  expect(seen, "not visible");
  expect(!("user_id" in seen), "user_id exposed");
  return `visible after ${Math.round(performance.now() - t0)} ms, no user_id`;
});

await check("UC2", "I2.4", "Mobile → Backend", "Login with wrong password", () =>
  rejects(B.api.login(emailA, "forkert"), /Invalid email or password/)
);

await check("UC2", "I2.5", "Mobile → Backend", "Invalid report (missing coordinates)", () =>
  rejects(A.api.submitReport({ type: "theft" }), /Field required; Field required/)
);

await check("UC2", "I2.6", "Mobile → Backend → Datalag", "Another user confirms the report (F3)", async () => {
  const { access_token } = await B.api.signup(unique(), "hemmeligt");
  B.setAuthToken(access_token);
  const confirmed = await B.api.confirmReport(created.id);
  expect(confirmed.confirmations === 1, `confirmations ${confirmed.confirmations}`);
  return "confirmations 0 → 1";
});

await check("UC2", "I2.7", "Mobile → Backend → Datalag", "Same user confirms again", () =>
  rejects(B.api.confirmReport(created.id), /already confirmed/)
);

await check("UC2", "I2.8", "Mobile → Backend", "Reporter confirms own report (F3)", () =>
  rejects(A.api.confirmReport(created.id), /own report/)
);

await check("UC2", "I2.9", "Mobile → Backend → Datalag", "NF10: rate limit on reports", async () => {
  let accepted = 1; // I2.2
  for (;;) {
    try {
      await A.api.submitReport(report);
      accepted += 1;
      expect(accepted <= 20, "no limit after 20 reports");
    } catch (e) {
      expect(/Too many reports/.test(e.message), `wrong error: ${e.message}`);
      return `${accepted} accepted, then: "${e.message}"`;
    }
  }
});

// --- Other interfaces ---
await check("Other", "I3.1", "Mobile → Backend → DST cache", "getZones (Aarhus bbox)", async () => {
  let zones = [];
  for (let i = 0; i < 30 && zones.length === 0; i++) {
    zones = await A.api.getZones(AARHUS_BBOX); // the Async Worker loads DST data after startup
    if (zones.length === 0) await sleep(2000);
  }
  expect(zones.length > 0, "zone cache still empty after 60 s");
  const status = await (await fetch(`${URL_A}/api/zones/status`)).json();
  return `${status.municipalities_cached} polygons cached; ${zones.length} in the Aarhus bbox`;
});

await check("Other", "I3.2", "Mobile ↔ Backend WebSocket", "openZonesFeed connects", async () => {
  const socket = A.openZonesFeed(() => {});
  const opened = await new Promise((resolve) => {
    socket.onopen = () => resolve(true);
    socket.onerror = () => resolve(false);
    setTimeout(() => resolve(false), 5000);
  });
  socket.close();
  expect(opened, "no connection");
  return "connected; events arrive when the Async Worker refreshes zones";
});

await check("Other", "I3.3", "Mobile → Backend → RSS + archive", "getNews", async () => {
  const news = await A.api.getNews();
  expect(news.length > 0, "no news");
  return `${news.length} items, ${news.filter((n) => n.latitude != null).length} with a position`;
});

// ---------------------------------------------------------------------------
console.log(`\nIntegration test — ${new Date().toISOString()} — Node ${process.version}\n`);
for (const table of ["UC1", "UC2", "Other"]) {
  console.log(`| ID | Interface | Test | Result | Status |\n|---|---|---|---|---|`);
  for (const r of results.filter((x) => x.table === table)) {
    console.log(`| ${r.id} | ${r.iface} | ${r.title} | ${r.detail} | ${r.ok ? "✓" : "✗"} |`);
  }
  console.log("");
}
const passed = results.filter((r) => r.ok).length;
console.log(`${passed} of ${results.length} passed.`);
process.exit(passed === results.length ? 0 : 1);
