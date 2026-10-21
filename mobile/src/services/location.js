// Boundary to the phone's location service (expo-location) for one-off
// position lookups — UC1 step 2 ("use my location") and UC2 step 2 (a
// report is placed at the user's current position). Continuous tracking
// during a walk is geofence.js's job.
import * as Location from "expo-location";

// NF2: 10-20 m in a city. "High" is GPS-level (~10 m); "Balanced" is only ~100 m.
export const POSITION_ACCURACY = Location.Accuracy.High;

/**
 * The user's current position as { latitude, longitude }, or null if
 * location permission isn't (or, with ask=false, isn't already) granted —
 * UC1/UC2 extension 2a: callers then let the user search manually or explain.
 */
export async function getCurrentCoordinates({ ask = true } = {}) {
  const { status } = ask
    ? await Location.requestForegroundPermissionsAsync()
    : await Location.getForegroundPermissionsAsync();
  if (status !== "granted") return null;

  const { coords } = await Location.getCurrentPositionAsync({ accuracy: POSITION_ACCURACY });
  return { latitude: coords.latitude, longitude: coords.longitude };
}

// For continuous tracking (geofence.js): ask once, report whether granted.
export async function requestLocationPermission() {
  const { status } = await Location.requestForegroundPermissionsAsync();
  return status === "granted";
}
