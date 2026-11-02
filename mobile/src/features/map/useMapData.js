import { useCallback, useEffect, useRef, useState } from "react";
import { AppState } from "react-native";

import { api } from "../../services/api";
import { zonesToGeofences } from "../../services/geofence";

// F7: only areas with an actual signal are coloured; "safe" stays uncoloured.
const COLOURED_ZONE_LABELS = ["unsafe", "mixed"];

// US-56: wait this long after the map stops moving before refetching, so a
// pan doesn't fire a request per frame.
export const REGION_DEBOUNCE_MS = 500;
// NF4 / US-16: new reports from others show up within 2 minutes.
export const REPORT_REFRESH_MS = 2 * 60 * 1000;

// Bounding box string for the Backend API: minLon,minLat,maxLon,maxLat.
export function regionToBbox(region) {
  return [
    region.longitude - region.longitudeDelta,
    region.latitude - region.latitudeDelta,
    region.longitude + region.longitudeDelta,
    region.latitude + region.latitudeDelta,
  ].join(",");
}

/**
 * Everything the map shows, fetched via services/api:
 *  - news pins: nationwide, for the chosen year range (`newsPeriod`,
 *    { from, to }); refetched when the range changes,
 *  - incidents, community reports and colour-coded zones (F7): for the
 *    visible region, refetched (debounced) whenever the map stops moving
 *    (US-56); reports also every 2 min while the app is in front (NF4).
 * Failures leave the list empty rather than breaking the map (NF7).
 */
export function useMapData(region, newsPeriod) {
  const [incidents, setIncidents] = useState([]);
  const [reports, setReports] = useState([]);
  const [zones, setZones] = useState([]);
  const [newsPins, setNewsPins] = useState([]);
  const bboxRef = useRef(regionToBbox(region));

  useEffect(() => {
    if (!newsPeriod) return;
    let cancelled = false;
    api
      .getNewsPins(newsPeriod)
      .then((items) => !cancelled && setNewsPins(items.filter((item) => item.latitude != null)))
      .catch(() => !cancelled && setNewsPins([]));
    return () => {
      cancelled = true;
    };
  }, [newsPeriod?.from, newsPeriod?.to]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadReports = useCallback(() => {
    api.getReports(bboxRef.current).then(setReports).catch(() => {}); // keep the last list on a failed refresh
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      const bbox = regionToBbox(region);
      bboxRef.current = bbox;
      api.getIncidents(bbox).then(setIncidents).catch(() => setIncidents([]));
      loadReports();
      api
        .getZones(bbox)
        .then((data) => setZones(zonesToGeofences(data, { labels: COLOURED_ZONE_LABELS })))
        .catch(() => setZones([]));
    }, REGION_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [region, loadReports]); // a new region object arrives only when the map stops moving

  // Periodic report refresh, paused while the app is in the background.
  useEffect(() => {
    let interval = setInterval(loadReports, REPORT_REFRESH_MS);
    const sub = AppState.addEventListener("change", (state) => {
      clearInterval(interval);
      if (state === "active") {
        loadReports();
        interval = setInterval(loadReports, REPORT_REFRESH_MS);
      }
    });
    return () => {
      clearInterval(interval);
      sub.remove();
    };
  }, [loadReports]);

  const addReport = (report) => setReports((prev) => [...prev, report]);
  const replaceReport = (report) => setReports((prev) => prev.map((r) => (r.id === report.id ? report : r)));

  return { incidents, reports, zones, newsPins, addReport, replaceReport };
}
