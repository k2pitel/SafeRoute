import { useEffect, useRef, useState } from "react";
import { StyleSheet, View, Text, TouchableOpacity, Linking } from "react-native";
import MapView, { Marker, Polygon, Polyline } from "react-native-maps";
import * as Location from "expo-location";
import { Ionicons } from "@expo/vector-icons";

import { api, openZonesFeed } from "../services/api";
import { useActiveRoute } from "../context/ActiveRouteContext";

// README > Mobile App — Pages > 1. Home / Map Page
// Shows crime pins (X = Crimes), color-coded safety zones, and the
// current fast-vs-safe route comparison drawn on the map.
export default function MapScreen() {
  const mapRef = useRef(null);
  const [region, setRegion] = useState({
    latitude: 56.1629, // Aarhus, Denmark, as a sensible default
    longitude: 10.2039,
    latitudeDelta: 0.05,
    longitudeDelta: 0.05,
  });
  const [incidents, setIncidents] = useState([]);
  const [zones, setZones] = useState([]);
  const [newsPins, setNewsPins] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [selectedNews, setSelectedNews] = useState(null);
  const wsRef = useRef(null);
  const { activeRoute } = useActiveRoute();

  // Crime news is nationwide, not tied to the current map viewport, so it's
  // fetched once rather than re-fetched on every region change.
  useEffect(() => {
    api
      .getNews()
      .then((items) => setNewsPins(items.filter((item) => item.latitude != null)))
      .catch(() => setNewsPins([]));
  }, []);

  const goToMyLocation = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") return;
    const loc = await Location.getCurrentPositionAsync({});
    const next = {
      latitude: loc.coords.latitude,
      longitude: loc.coords.longitude,
      latitudeDelta: 0.02,
      longitudeDelta: 0.02,
    };
    setRegion(next);
    mapRef.current?.animateToRegion(next, 400);
  };

  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === "granted") {
        const loc = await Location.getCurrentPositionAsync({});
        setRegion((r) => ({ ...r, latitude: loc.coords.latitude, longitude: loc.coords.longitude }));
      }
    })();
  }, []);

  useEffect(() => {
    const bbox = [
      region.longitude - region.longitudeDelta,
      region.latitude - region.latitudeDelta,
      region.longitude + region.longitudeDelta,
      region.latitude + region.latitudeDelta,
    ].join(",");

    api.getIncidents(bbox).then(setIncidents).catch(() => setIncidents([]));
    api.getZones(bbox).then(setZones).catch(() => setZones([]));

    // Live safety-score/zone updates over WebSocket — README > System Architecture.
    wsRef.current = openZonesFeed((update) => {
      // Zones shifting color in real time (e.g. time-of-day changes) would
      // be applied to a zones layer here.
      console.log("Zone update:", update);
    });
    return () => wsRef.current?.close();
  }, [region.latitude, region.longitude]);

  // Draw the route picked on the Route tab, and fit the camera to it.
  const routeCoords = activeRoute?.option.geometry.coordinates.map(([longitude, latitude]) => ({
    latitude,
    longitude,
  }));

  useEffect(() => {
    if (routeCoords && routeCoords.length > 1 && mapRef.current) {
      mapRef.current.fitToCoordinates(routeCoords, {
        edgePadding: { top: 80, right: 60, bottom: 80, left: 60 },
        animated: true,
      });
    }
  }, [activeRoute]); // eslint-disable-line react-hooks/exhaustive-deps

  const routeColor = activeRoute && activeRoute.option.safety_score >= 6.5 ? "#0EA47A" : "#E5484D";

  // README > Home/Map Page: 🔴 unsafe, 🟡 mixed/uncertain, no color = no signal.
  const ZONE_COLORS = {
    unsafe: { fill: "rgba(229,72,77,0.25)", stroke: "rgba(229,72,77,0.8)" },
    mixed: { fill: "rgba(240,180,41,0.25)", stroke: "rgba(240,180,41,0.85)" },
  };

  return (
    <View style={styles.container}>
      <MapView ref={mapRef} style={styles.map} initialRegion={region} showsUserLocation>
        {zones
          .filter((zone) => ZONE_COLORS[zone.safety_label])
          .map((zone) => (
            <Polygon
              key={zone.id}
              coordinates={zone.geometry.coordinates[0].map(([longitude, latitude]) => ({ latitude, longitude }))}
              fillColor={ZONE_COLORS[zone.safety_label].fill}
              strokeColor={ZONE_COLORS[zone.safety_label].stroke}
              strokeWidth={2}
            />
          ))}

        {incidents.map((incident) => (
          <Marker
            key={`incident-${incident.id}`}
            coordinate={{ latitude: incident.latitude, longitude: incident.longitude }}
            pinColor="red"
            onPress={() => {
              setSelectedNews(null);
              setSelectedIncident(incident);
            }}
          />
        ))}

        {newsPins.map((item) => (
          <Marker
            key={`news-${item.url}`}
            coordinate={{ latitude: item.latitude, longitude: item.longitude }}
            pinColor="orange"
            onPress={() => {
              setSelectedIncident(null);
              setSelectedNews(item);
            }}
          />
        ))}

        {routeCoords && <Polyline coordinates={routeCoords} strokeColor={routeColor} strokeWidth={5} />}
        {activeRoute?.destination && (
          <Marker
            coordinate={{
              latitude: activeRoute.destination.latitude,
              longitude: activeRoute.destination.longitude,
            }}
            pinColor="#007AFF"
            title={activeRoute.destination.label}
          />
        )}
      </MapView>

      {(zones.length > 0 || newsPins.length > 0) && (
        <View style={styles.legend}>
          {zones.length > 0 && (
            <>
              <View style={styles.legendRow}>
                <View style={[styles.legendDot, { backgroundColor: "#E5484D" }]} />
                <Text style={styles.legendText}>Unsafe zone</Text>
              </View>
              <View style={styles.legendRow}>
                <View style={[styles.legendDot, { backgroundColor: "#F0B429" }]} />
                <Text style={styles.legendText}>Mixed / uncertain</Text>
              </View>
            </>
          )}
          {newsPins.length > 0 && (
            <View style={styles.legendRow}>
              <View style={[styles.legendDot, { backgroundColor: "orange" }]} />
              <Text style={styles.legendText}>Crime news</Text>
            </View>
          )}
        </View>
      )}

      <TouchableOpacity style={styles.locateFab} onPress={goToMyLocation}>
        <Ionicons name="locate" size={24} color="#007AFF" />
      </TouchableOpacity>

      {activeRoute && (
        <View style={styles.routeBanner}>
          <Text style={styles.routeBannerText}>
            {Math.round(activeRoute.option.duration_minutes)} min · Safety: {activeRoute.option.safety_label} (
            {activeRoute.option.safety_score.toFixed(1)}/10)
          </Text>
        </View>
      )}

      {selectedIncident && (
        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>{selectedIncident.type}</Text>
          <Text>Date: {new Date(selectedIncident.occurred_at).toLocaleString()}</Text>
          <Text>Info: {selectedIncident.description}</Text>
          <TouchableOpacity onPress={() => setSelectedIncident(null)}>
            <Text style={styles.close}>Close</Text>
          </TouchableOpacity>
        </View>
      )}

      {selectedNews && (
        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>{selectedNews.title}</Text>
          <Text>
            {selectedNews.source} · {new Date(selectedNews.published_at).toLocaleDateString()}
          </Text>
          <View style={styles.newsActions}>
            <TouchableOpacity onPress={() => Linking.openURL(selectedNews.url)}>
              <Text style={styles.close}>Open article</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setSelectedNews(null)}>
              <Text style={styles.close}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
  locateFab: {
    position: "absolute",
    right: 16,
    bottom: 100,
    backgroundColor: "white",
    borderRadius: 24,
    padding: 10,
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  routeBanner: {
    position: "absolute",
    top: 12,
    left: 20,
    right: 20,
    backgroundColor: "white",
    borderRadius: 10,
    padding: 10,
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  routeBannerText: { textAlign: "center", fontWeight: "600" },
  legend: {
    position: "absolute",
    left: 16,
    bottom: 100,
    backgroundColor: "white",
    borderRadius: 10,
    padding: 10,
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  legendRow: { flexDirection: "row", alignItems: "center", marginVertical: 2 },
  legendDot: { width: 10, height: 10, borderRadius: 5, marginRight: 8 },
  legendText: { fontSize: 12, color: "#333" },
  infoCard: {
    position: "absolute",
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: "white",
    borderRadius: 12,
    padding: 16,
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  infoTitle: { fontWeight: "bold", fontSize: 16, marginBottom: 4, textTransform: "capitalize" },
  close: { color: "#007AFF", marginTop: 8 },
  newsActions: { flexDirection: "row", justifyContent: "space-between" },
});
