// README > Bonus: Geofenced Push Notifications
// Watches the user's live location against known red-zone polygons and
// time-of-day thresholds, and fires local push notifications.
import * as Location from "expo-location";
import * as Notifications from "expo-notifications";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

// Simple point-in-polygon check (ray casting) — no extra deps required.
function isInsidePolygon(point, polygon) {
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

async function notify(title, body) {
  await Notifications.scheduleNotificationAsync({
    content: { title, body },
    trigger: null, // fire immediately
  });
}

/**
 * Starts watching the user's position. Call once (e.g. from a top-level
 * effect) with the current list of red-zone polygons (fetched/streamed
 * from the backend's /ws/zones or /api/incidents-derived zones).
 */
export function startGeofenceWatch(redZones) {
  let lastZoneState = false;
  let lastHourAlerted = null;

  return Location.watchPositionAsync(
    { accuracy: Location.Accuracy.Balanced, timeInterval: 15000, distanceInterval: 25 },
    async (position) => {
      const point = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      };

      // Red zone entry check
      const inRedZone = redZones.some((zone) => isInsidePolygon(point, zone.polygon));
      if (inRedZone && !lastZoneState) {
        await notify("You have entered a dangerous zone", "Please be aware of your surroundings.");
      }
      lastZoneState = inRedZone;

      // Time-based check (e.g. flag late-night hours)
      const hour = new Date().getHours();
      const isLateNight = hour >= 0 && hour < 5;
      if (isLateNight && lastHourAlerted !== hour) {
        await notify(
          `It's now ${hour}:00`,
          "Bad activities happen more often at this time — please be careful."
        );
        lastHourAlerted = hour;
      }
    }
  );
}
