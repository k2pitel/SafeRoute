import { useEffect, useState } from "react";

import { api } from "../../services/api";
import { zonesToGeofences } from "../../services/geofence";

// F7: only areas with an actual signal are coloured; "safe" stays uncoloured.
const COLOURED_ZONE_LABELS = ["unsafe", "mixed"];

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
 *  - news pins: nationwide, fetched once for all archived years,
 *  - incidents, community reports and colour-coded zones (F7): for the
 *    visible region, refetched when the map centre moves (NF4: new reports
 *    show up on the next fetch).
 * Failures leave the list empty rather than breaking the map (NF7).
 */
export function useMapData(region) {
  const [incidents, setIncidents] = useState([]);
  const [reports, setReports] = useState([]);
  const [zones, setZones] = useState([]);
  const [newsPins, setNewsPins] = useState([]);

  useEffect(() => {
    api
      .getNewsAllYears()
      .then((items) => setNewsPins(items.filter((item) => item.latitude != null)))
      .catch(() => setNewsPins([]));
  }, []);

  useEffect(() => {
    const bbox = regionToBbox(region);
    api.getIncidents(bbox).then(setIncidents).catch(() => setIncidents([]));
    api.getReports(bbox).then(setReports).catch(() => setReports([]));
    api
      .getZones(bbox)
      .then((data) => setZones(zonesToGeofences(data, { labels: COLOURED_ZONE_LABELS })))
      .catch(() => setZones([]));
    // Refetch only when the map centre moves, not on zoom alone (deltas).
  }, [region.latitude, region.longitude]); // eslint-disable-line react-hooks/exhaustive-deps

  const addReport = (report) => setReports((prev) => [...prev, report]);
  const replaceReport = (report) => setReports((prev) => prev.map((r) => (r.id === report.id ? report : r)));

  return { incidents, reports, zones, newsPins, addReport, replaceReport };
}
