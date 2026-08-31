import { useEffect, useState } from "react";
import { StyleSheet, View, Text, TouchableOpacity, FlatList } from "react-native";
import { useNavigation } from "@react-navigation/native";
import * as Location from "expo-location";
import { Ionicons } from "@expo/vector-icons";

import { api } from "../services/api";
import { useActiveRoute } from "../context/ActiveRouteContext";
import PlaceSearchInput from "../components/PlaceSearchInput";

// README > Mobile App — Pages > 2. Route Page
// From/To place search, sortable list of route options with time + safety
// label. Picking a route draws it on the Map tab.
export default function RouteScreen() {
  const navigation = useNavigation();
  const { setActiveRoute } = useActiveRoute();

  const [origin, setOrigin] = useState(null); // { latitude, longitude, label }
  const [destination, setDestination] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [sortBy, setSortBy] = useState("safety"); // 'safety' | 'time'
  const [loading, setLoading] = useState(false);
  const [locating, setLocating] = useState(false);
  const [myLocation, setMyLocation] = useState(null);

  // Silently grab a location fix (if permission's already granted) so
  // search results can be biased toward it from the very first keystroke,
  // like a train app's station picker prioritizing nearby stops.
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
    navigation.navigate("Map");
  };

  const sorted = [...routes].sort((a, b) =>
    sortBy === "time" ? a.duration_minutes - b.duration_minutes : b.safety_score - a.safety_score
  );

  return (
    <View style={styles.container}>
      <PlaceSearchInput
        placeholder="From"
        value={origin?.primary || origin?.label}
        onSelect={setOrigin}
        near={myLocation}
        rightAccessory={
          <TouchableOpacity style={styles.locateButton} onPress={useMyLocation} disabled={locating}>
            <Ionicons name="locate" size={20} color="#007AFF" />
          </TouchableOpacity>
        }
      />
      <View style={{ height: 8 }} />
      <PlaceSearchInput
        placeholder="To"
        value={destination?.primary || destination?.label}
        onSelect={setDestination}
        near={origin || myLocation}
      />

      <TouchableOpacity
        style={[styles.button, (!origin || !destination) && styles.buttonDisabled]}
        onPress={search}
        disabled={!origin || !destination}
      >
        <Text style={styles.buttonText}>{loading ? "Searching…" : "Find routes"}</Text>
      </TouchableOpacity>

      <View style={styles.sortRow}>
        <TouchableOpacity onPress={() => setSortBy("time")}>
          <Text style={sortBy === "time" ? styles.sortActive : styles.sort}>Sort by time</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setSortBy("safety")}>
          <Text style={sortBy === "safety" ? styles.sortActive : styles.sort}>Sort by safety</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={sorted}
        keyExtractor={(_, i) => String(i)}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.routeCard} onPress={() => pickRoute(item)}>
            <Text style={styles.duration}>{Math.round(item.duration_minutes)} min</Text>
            <Text style={styles.safety}>
              Safety: {item.safety_label} ({item.safety_score.toFixed(1)}/10)
            </Text>
            <Text style={styles.showOnMap}>Tap to show on map →</Text>
          </TouchableOpacity>
        )}
        ListEmptyComponent={<Text style={styles.empty}>Search a from/to to see route options.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  locateButton: { padding: 8 },
  button: { backgroundColor: "#007AFF", borderRadius: 8, padding: 12, alignItems: "center", marginVertical: 16 },
  buttonDisabled: { backgroundColor: "#a9c9ef" },
  buttonText: { color: "white", fontWeight: "600" },
  sortRow: { flexDirection: "row", justifyContent: "space-around", marginBottom: 12 },
  sort: { color: "#666" },
  sortActive: { color: "#007AFF", fontWeight: "700" },
  routeCard: { borderWidth: 1, borderColor: "#eee", borderRadius: 10, padding: 14, marginBottom: 10 },
  duration: { fontSize: 18, fontWeight: "700" },
  safety: { color: "#444", marginTop: 4 },
  showOnMap: { color: "#007AFF", marginTop: 6, fontSize: 12 },
  empty: { textAlign: "center", color: "#999", marginTop: 40 },
});
