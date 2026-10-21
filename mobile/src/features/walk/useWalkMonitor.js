import { useEffect } from "react";

import { api, openZonesFeed } from "../../services/api";
import { ensureNotificationPermission, startGeofenceWatch, zonesToGeofences } from "../../services/geofence";
import { requestLocationPermission } from "../../services/location";
import { useSettings } from "../settings/SettingsContext";

// Margin around the route when fetching zones, so a small detour off the
// route is still covered (~1 km).
const ZONE_MARGIN_DEGREES = 0.01;

// minLon,minLat,maxLon,maxLat around a GeoJSON line ([lon, lat] points).
export function routeBbox(coordinates, margin = ZONE_MARGIN_DEGREES) {
  const lons = coordinates.map(([lon]) => lon);
  const lats = coordinates.map(([, lat]) => lat);
  return [
    Math.min(...lons) - margin,
    Math.min(...lats) - margin,
    Math.max(...lons) + margin,
    Math.max(...lats) + margin,
  ].join(",");
}

/**
 * F5: real-time monitoring while the active route is walked (afsnit 4.2.2).
 * Fetches the route area's zone polygons once (GET /api/zones), evaluates
 * zone entry + time of day locally on every position update
 * (services/geofence) and refetches when /ws/zones reports changed zones —
 * the position itself never leaves the phone (NF11). Honours the alert
 * switches in Settings (F6). Stops when the route is cleared or replaced.
 */
export function useWalkMonitor(activeRoute) {
  const { settings } = useSettings();
  const { zoneAlerts, timeAlerts } = settings;

  useEffect(() => {
    if (!activeRoute || (!zoneAlerts && !timeAlerts)) return undefined;

    let cancelled = false;
    let watch = null;
    let socket = null;
    const bbox = routeBbox(activeRoute.option.geometry.coordinates);

    const startWatch = async () => {
      const zones = await api.getZones(bbox).catch(() => []); // NF7: no zones -> time alerts still work
      if (cancelled) return;
      const next = await startGeofenceWatch(zonesToGeofences(zones), { zoneAlerts, timeAlerts });
      watch?.remove();
      watch = next;
      if (cancelled) watch.remove();
    };

    (async () => {
      const allowed = (await requestLocationPermission()) && (await ensureNotificationPermission());
      if (!allowed || cancelled) return;
      await startWatch();
      socket = openZonesFeed((event) => {
        if (event.type === "zones_refreshed") startWatch();
      });
    })().catch((e) => console.warn("Walk monitoring could not start", e));

    return () => {
      cancelled = true;
      watch?.remove();
      socket?.close();
    };
  }, [activeRoute, zoneAlerts, timeAlerts]);
}
