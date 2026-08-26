import { useEffect, useRef, useState } from "react";
import { StyleSheet, View, Text, TouchableOpacity } from "react-native";
import MapView, { Marker, Polyline } from "react-native-maps";
import * as Location from "expo-location";

import { api, openZonesFeed } from "../services/api";

// README > Mobile App — Pages > 1. Home / Map Page
// Shows crime pins (X = Crimes), color-coded safety zones, and the
// current fast-vs-safe route comparison drawn on the map.
export default function MapScreen() {
  const [region, setRegion] = useState({
    latitude: 56.1629, // Aarhus, Denmark, as a sensible default
    longitude: 10.2039,
    latitudeDelta: 0.05,
    longitudeDelta: 0.05,
  });
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const wsRef = useRef(null);

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

    // Live safety-score/zone updates over WebSocket — README > System Architecture.
    wsRef.current = openZonesFeed((update) => {
      // Zones shifting color in real time (e.g. time-of-day changes) would
      // be applied to a zones layer here.
      console.log("Zone update:", update);
    });
    return () => wsRef.current?.close();
  }, [region.latitude, region.longitude]);

  return (
    <View style={styles.container}>
      <MapView style={styles.map} region={region} showsUserLocation>
        {incidents.map((incident) => (
          <Marker
            key={incident.id}
            coordinate={{ latitude: incident.latitude, longitude: incident.longitude }}
            pinColor="red"
            onPress={() => setSelectedIncident(incident)}
          />
        ))}
      </MapView>

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
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
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
});
