import { useEffect, useState } from "react";
import { StyleSheet, View, Text, TouchableOpacity, ScrollView } from "react-native";
import * as Location from "expo-location";
import { Ionicons } from "@expo/vector-icons";

import { api } from "../services/api";
import { useActiveRoute } from "../context/ActiveRouteContext";
import PlaceSearchInput from "./PlaceSearchInput";

// Compact From/To route picker that sits above the map (DSB-app style)
// instead of living on its own tab. Collapsed by default to a single bar;
// tapping it opens the search fields + route list, and picking an option
// collapses it again — the route itself is drawn by MapScreen, which reads
// it straight off ActiveRouteContext.
export default function RoutePanel() {
  const { activeRoute, setActiveRoute } = useActiveRoute();

  const [expanded, setExpanded] = useState(false);
  const [origin, setOrigin] = useState(null);
  const [destination, setDestination] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [sortBy, setSortBy] = useState("safety"); // 'safety' | 'time'
  const [loading, setLoading] = useState(false);
  const [locating, setLocating] = useState(false);
  const [myLocation, setMyLocation] = useState(null);

  useEffect(() => {
    (async () => {
      const { status } = await Location.getForegroundPermissionsAsync();
      if (status !== "granted") return;
      const loc = await Location.getCurrentPositionAsync({});
      setMyLocation({ latitude: loc.coords.latitude, longitude: loc.coords.longitude });
    })();
  }, []);

  const useMyLocation = async () => {
    setLocating(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") return;
      const loc = await Location.getCurrentPositionAsync({});
      const coords = { latitude: loc.coords.latitude, longitude: loc.coords.longitude };
      setMyLocation(coords);
      setOrigin({ ...coords, label: "My location" });
    } finally {
      setLocating(false);
    }
  };

  const search = async () => {
    if (!origin || !destination) return;
    setLoading(true);
    try {
      const from = `${origin.latitude},${origin.longitude}`;
      const to = `${destination.latitude},${destination.longitude}`;
      const results = await api.getRoutes(from, to);
      setRoutes(results);
    } catch (e) {
      console.warn("Route search failed", e);
      setRoutes([]);
    } finally {
      setLoading(false);
    }
  };

  const pickRoute = (option) => {
    setActiveRoute({ origin, destination, option });
    setExpanded(false);
  };

  const swapOriginAndDestination = () => {
    setOrigin(destination);
    setDestination(origin);
    setRoutes([]); // stale results no longer match the swapped from/to
  };

  const sorted = [...routes].sort((a, b) =>
    sortBy === "time" ? a.duration_minutes - b.duration_minutes : b.safety_score - a.safety_score
  );

  if (!expanded) {
    return (
      <TouchableOpacity style={styles.collapsedBar} onPress={() => setExpanded(true)}>
        {activeRoute && (
          <Text style={styles.collapsedText} numberOfLines={1}>
            {`${Math.round(activeRoute.option.duration_minutes)} min · Safety: ${activeRoute.option.safety_label} (${activeRoute.option.safety_score.toFixed(1)}/10)`}
          </Text>
        )}
        <Ionicons name="chevron-down" size={20} color="#666" />
      </TouchableOpacity>
    );
  }

  return (
    <View style={styles.panel}>
      <TouchableOpacity style={styles.header} onPress={() => setExpanded(false)}>
        <Ionicons name="chevron-up" size={20} color="#666" />
      </TouchableOpacity>

      <View style={styles.fieldsRow}>
        <View style={styles.fieldsColumn}>
          <PlaceSearchInput
            placeholder="From"
            value={origin?.primary || origin?.label}
            onSelect={setOrigin}
            near={myLocation}
          />
          <View style={{ height: 6 }} />
          <PlaceSearchInput
            placeholder="To"
            value={destination?.primary || destination?.label}
            onSelect={setDestination}
            near={origin || myLocation}
          />
        </View>

        <View style={styles.sideButtons}>
          <TouchableOpacity style={styles.sideButton} onPress={useMyLocation} disabled={locating}>
            <Ionicons name="locate" size={18} color="#007AFF" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.sideButton}
            onPress={swapOriginAndDestination}
            disabled={!origin && !destination}
          >
            <Ionicons name="swap-vertical" size={18} color={origin || destination ? "#007AFF" : "#ccc"} />
          </TouchableOpacity>
        </View>
      </View>

      <TouchableOpacity
        style={[styles.button, (!origin || !destination) && styles.buttonDisabled]}
        onPress={search}
        disabled={!origin || !destination}
      >
        <Text style={styles.buttonText}>{loading ? "Searching…" : "Find routes"}</Text>
      </TouchableOpacity>

      {routes.length > 0 && (
        <>
          <View style={styles.sortRow}>
            <TouchableOpacity onPress={() => setSortBy("time")}>
              <Text style={sortBy === "time" ? styles.sortActive : styles.sort}>Sort by time</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setSortBy("safety")}>
              <Text style={sortBy === "safety" ? styles.sortActive : styles.sort}>Sort by safety</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.results} nestedScrollEnabled>
            {sorted.map((item, i) => (
              <TouchableOpacity key={i} style={styles.routeCard} onPress={() => pickRoute(item)}>
                <Text style={styles.duration}>{Math.round(item.duration_minutes)} min</Text>
                <Text style={styles.safety}>
                  Safety: {item.safety_label} ({item.safety_score.toFixed(1)}/10)
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  collapsedBar: {
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "white",
    paddingVertical: 8,
    paddingHorizontal: 14,
    gap: 4,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
  },
  collapsedText: { color: "#333", fontSize: 13, fontWeight: "500" },
  panel: {
    backgroundColor: "white",
    paddingHorizontal: 14,
    paddingTop: 10,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
    maxHeight: 340,
  },
  header: { alignItems: "center", justifyContent: "center", paddingVertical: 2, marginBottom: 6 },
  fieldsRow: { flexDirection: "row", alignItems: "stretch" },
  fieldsColumn: { flex: 1 },
  sideButtons: { justifyContent: "space-between", marginLeft: 8 },
  sideButton: { padding: 6 },
  button: { backgroundColor: "#007AFF", borderRadius: 8, padding: 10, alignItems: "center", marginTop: 10 },
  buttonDisabled: { backgroundColor: "#a9c9ef" },
  buttonText: { color: "white", fontWeight: "600", fontSize: 13 },
  sortRow: { flexDirection: "row", justifyContent: "space-around", marginTop: 10, marginBottom: 6 },
  sort: { color: "#666", fontSize: 12 },
  sortActive: { color: "#007AFF", fontWeight: "700", fontSize: 12 },
  results: { maxHeight: 150 },
  routeCard: { borderWidth: 1, borderColor: "#eee", borderRadius: 10, padding: 10, marginBottom: 6 },
  duration: { fontSize: 15, fontWeight: "700" },
  safety: { color: "#444", marginTop: 2, fontSize: 12 },
});
