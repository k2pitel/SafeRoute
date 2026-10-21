// Client-side geofencing for F5 (afsnit 4.2.2): watches the user's live
// position against cached zone polygons and the time of day, and fires
// local notifications — without a round trip to the Backend API, so the
// alert's latency is bound by the phone's own position updates (NF3) and
// the server never receives a continuous location stream (NF11).
import * as Location from "expo-location";
import * as Notifications from "expo-notifications";

import { POSITION_ACCURACY } from "./location";

// NF3: a position update at least every 15 s or every 25 m of movement;
// NF2: GPS-level accuracy, or zone entry can't be decided reliably.
const WATCH_OPTIONS = { accuracy: POSITION_ACCURACY, timeInterval: 15000, distanceInterval: 25 };

// Hours (local time) at which the time condition alerts, once per new hour.
const LATE_NIGHT_START_HOUR = 0;
const LATE_NIGHT_END_HOUR = 5;

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

// Point-in-polygon check (ray casting) — no extra deps required.
// polygon: [{ latitude, longitude }, ...]
export function isInsidePolygon(point, polygon) {
  const { latitude: y, longitude: x } = point;
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].longitude, yi = polygon[i].latitude;
    const xj = polygon[j].longitude, yj = polygon[j].latitude;
    const intersect =
      yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

/**
 * Adapter from GET /api/zones (GeoJSON Polygon/MultiPolygon with [lon, lat]
 * rings) to the geofence's own zone shape { id, polygon: [{latitude,
 * longitude}] }. Only the outer ring of each polygon is used — holes are
 * ignored, which errs on the side of alerting. A MultiPolygon becomes one
 * zone per part.
 */
export function zonesToGeofences(zones, { labels = ["unsafe"] } = {}) {
  const toRing = (ring) => ring.map(([longitude, latitude]) => ({ latitude, longitude }));
  const geofences = [];
  for (const zone of zones) {
    if (!labels.includes(zone.safety_label)) continue;
    const { type, coordinates } = zone.geometry;
    const polygons = type === "MultiPolygon" ? coordinates : type === "Polygon" ? [coordinates] : [];
    polygons.forEach((rings, index) => {
      geofences.push({
        id: polygons.length > 1 ? `${zone.id}#${index}` : zone.id,
        label: zone.safety_label,
        polygon: toRing(rings[0]),
      });
    });
  }
  return geofences;
}

// Local notifications need the user's OK once (iOS always, Android 13+).
export async function ensureNotificationPermission() {
  const { status } = await Notifications.getPermissionsAsync();
  if (status === "granted") return true;
  const request = await Notifications.requestPermissionsAsync();
  return request.status === "granted";
}

async function notify(title, body) {
  await Notifications.scheduleNotificationAsync({
    content: { title, body },
    trigger: null, // fire immediately
  });
}

/**
 * Starts watching the user's position while a route is walked. Evaluates
 * two independent conditions per position update:
 *  - zone: notify on the transition from outside to inside a red zone,
 *  - time: notify once per new hour in the late-night window.
 * redZones: output of zonesToGeofences(). Each condition can be switched
 * off from the settings (F6). Resolves to a subscription whose .remove()
 * stops the watch.
 */
export function startGeofenceWatch(redZones, { zoneAlerts = true, timeAlerts = true } = {}) {
  let lastZoneState = false;
  let lastHourAlerted = null;

  return Location.watchPositionAsync(WATCH_OPTIONS, async (position) => {
    const point = {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
    };

    const inRedZone = redZones.some((zone) => isInsidePolygon(point, zone.polygon));
    if (zoneAlerts && inRedZone && !lastZoneState) {
      await notify("You have entered a dangerous zone", "Please be aware of your surroundings.");
    }
    lastZoneState = inRedZone;

    const hour = new Date().getHours();
    const isLateNight = hour >= LATE_NIGHT_START_HOUR && hour < LATE_NIGHT_END_HOUR;
    if (timeAlerts && isLateNight && lastHourAlerted !== hour) {
      await notify(
        `It's now ${hour}:00`,
        "Bad activities happen more often at this time — please be careful."
      );
      lastHourAlerted = hour;
    }
  });
}
