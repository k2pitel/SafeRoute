import { useEffect, useState } from "react";
import { StyleSheet, View, Text, FlatList, ActivityIndicator, Linking, TouchableOpacity } from "react-native";

import { api } from "../services/api";

// README > Mobile App — Pages > 3. Latest News Page
// City-scoped, crime-related news only.
export default function NewsScreen() {
  const [city, setCity] = useState("Aarhus, Denmark"); // TODO: derive from user location/settings
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getNews(city)
      .then(setNews)
      .catch(() => setNews([]))
      .finally(() => setLoading(false));
  }, [city]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Crime news — {city}</Text>
      <FlatList
        data={news}
        keyExtractor={(item) => item.url}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => Linking.openURL(item.url)}>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.meta}>
              {item.source} · {new Date(item.published_at).toLocaleDateString()}
            </Text>
            {item.summary ? <Text style={styles.summary}>{item.summary}</Text> : null}
          </TouchableOpacity>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No recent crime news for this city.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  header: { fontSize: 18, fontWeight: "700", marginBottom: 12 },
  card: { borderBottomWidth: 1, borderColor: "#eee", paddingVertical: 12 },
  title: { fontSize: 15, fontWeight: "600" },
  meta: { color: "#888", fontSize: 12, marginTop: 2 },
  summary: { color: "#444", marginTop: 6 },
  empty: { textAlign: "center", color: "#999", marginTop: 40 },
});
