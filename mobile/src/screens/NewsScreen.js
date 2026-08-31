import { useEffect, useState } from "react";
import { StyleSheet, View, Text, TextInput, FlatList, ActivityIndicator, Linking, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { api } from "../services/api";

// README > Mobile App — Pages > 3. Latest News Page
// Crime-related news, nationwide by default, optionally filtered to a city.
export default function NewsScreen() {
  const [city, setCity] = useState(""); // empty = all of Denmark
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = (cityFilter) => {
    setLoading(true);
    api
      .getNews(cityFilter || undefined)
      .then(setNews)
      .catch(() => setNews([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => load(city), []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Crime news — {city || "Denmark"}</Text>
      <TextInput
        style={styles.input}
        value={city}
        onChangeText={setCity}
        onSubmitEditing={() => load(city)}
        placeholder="Filter by city (optional)"
      />

      {loading ? (
        <ActivityIndicator style={{ marginTop: 20 }} />
      ) : (
        <FlatList
          data={news}
          keyExtractor={(item) => item.url}
          renderItem={({ item }) => (
            <TouchableOpacity style={styles.card} onPress={() => Linking.openURL(item.url)}>
              <View style={styles.titleRow}>
                <Text style={styles.title}>{item.title}</Text>
                {item.latitude != null && <Ionicons name="location" size={14} color="#E5484D" />}
              </View>
              <Text style={styles.meta}>
                {item.source} · {new Date(item.published_at).toLocaleDateString()}
              </Text>
              {item.summary ? <Text style={styles.summary}>{item.summary}</Text> : null}
            </TouchableOpacity>
          )}
          ListEmptyComponent={<Text style={styles.empty}>No recent crime news{city ? ` for ${city}` : ""}.</Text>}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  header: { fontSize: 18, fontWeight: "700", marginBottom: 8 },
  input: { borderWidth: 1, borderColor: "#ccc", borderRadius: 8, padding: 10, marginBottom: 12 },
  card: { borderBottomWidth: 1, borderColor: "#eee", paddingVertical: 12 },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  title: { fontSize: 15, fontWeight: "600", flexShrink: 1 },
  meta: { color: "#888", fontSize: 12, marginTop: 2 },
  summary: { color: "#444", marginTop: 6 },
  empty: { textAlign: "center", color: "#999", marginTop: 40 },
});
