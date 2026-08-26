import { useState } from "react";
import { StyleSheet, View, Text, TextInput, TouchableOpacity, FlatList } from "react-native";

import { api } from "../services/api";

// README > Mobile App — Pages > 2. Route Page
// From/To input, sortable list of route options with time + safety label.
export default function RouteScreen() {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [routes, setRoutes] = useState([]);
  const [sortBy, setSortBy] = useState("safety"); // 'safety' | 'time'
  const [loading, setLoading] = useState(false);

  const search = async () => {
    if (!from || !to) return;
    setLoading(true);
    try {
      const results = await api.getRoutes(from, to);
      setRoutes(results);
    } catch (e) {
      console.warn("Route search failed", e);
    } finally {
      setLoading(false);
    }
  };

  const sorted = [...routes].sort((a, b) =>
    sortBy === "time" ? a.duration_minutes - b.duration_minutes : b.safety_score - a.safety_score
  );

  return (
    <View style={styles.container}>
      <TextInput style={styles.input} placeholder="From (lat,lon)" value={from} onChangeText={setFrom} />
      <TextInput style={styles.input} placeholder="To (lat,lon)" value={to} onChangeText={setTo} />
      <TouchableOpacity style={styles.button} onPress={search}>
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
          <View style={styles.routeCard}>
            <Text style={styles.duration}>{Math.round(item.duration_minutes)} min</Text>
            <Text style={styles.safety}>
              Safety: {item.safety_label} ({item.safety_score.toFixed(1)}/10)
            </Text>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.empty}>Enter a from/to to see route options.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  input: { borderWidth: 1, borderColor: "#ccc", borderRadius: 8, padding: 10, marginBottom: 8 },
  button: { backgroundColor: "#007AFF", borderRadius: 8, padding: 12, alignItems: "center", marginBottom: 16 },
  buttonText: { color: "white", fontWeight: "600" },
  sortRow: { flexDirection: "row", justifyContent: "space-around", marginBottom: 12 },
  sort: { color: "#666" },
  sortActive: { color: "#007AFF", fontWeight: "700" },
  routeCard: { borderWidth: 1, borderColor: "#eee", borderRadius: 10, padding: 14, marginBottom: 10 },
  duration: { fontSize: 18, fontWeight: "700" },
  safety: { color: "#444", marginTop: 4 },
  empty: { textAlign: "center", color: "#999", marginTop: 40 },
});
