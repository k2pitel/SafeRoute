import { useEffect, useState } from "react";
import { StyleSheet, View, Text, TextInput, FlatList, ActivityIndicator, Linking, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { api } from "../../services/api";
import { colors, inputStyle, radius, spacing } from "../../theme";

// F9: crime-related news, nationwide by default, optionally filtered to a city.
// "Latest" pulls live feeds + recently-archived items; picking a year
// switches to browsing the historical archive instead (see
// backend/app/api/news/backfill.py for how 2020+ got in there).
const YEARS = ["Latest", 2026, 2025, 2024, 2023, 2022, 2021, 2020];

export default function NewsScreen() {
  const [city, setCity] = useState(""); // empty = all of Denmark
  const [year, setYear] = useState("Latest");
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = (cityFilter, yearFilter) => {
    setLoading(true);
    api
      .getNews(cityFilter || undefined, yearFilter === "Latest" ? undefined : yearFilter)
      .then(setNews)
      .catch(() => setNews([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => load(city, year), []); // eslint-disable-line react-hooks/exhaustive-deps

  const selectYear = (y) => {
    setYear(y);
    load(city, y);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Crime news — {city || "Denmark"}</Text>
      <TextInput
        style={styles.input}
        value={city}
        onChangeText={setCity}
        onSubmitEditing={() => load(city, year)}
        placeholder="Filter by city (optional)"
      />

      <FlatList
        horizontal
        showsHorizontalScrollIndicator={false}
        data={YEARS}
        keyExtractor={(y) => String(y)}
        style={styles.yearRow}
        renderItem={({ item: y }) => (
          <TouchableOpacity style={[styles.yearChip, y === year && styles.yearChipActive]} onPress={() => selectYear(y)}>
            <Text style={[styles.yearChipText, y === year && styles.yearChipTextActive]}>{y}</Text>
          </TouchableOpacity>
        )}
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
                {item.latitude != null && <Ionicons name="location" size={14} color={colors.danger} />}
              </View>
              <Text style={styles.meta}>
                {item.source} · {new Date(item.published_at).toLocaleDateString()}
              </Text>
              {item.summary ? <Text style={styles.summary}>{item.summary}</Text> : null}
            </TouchableOpacity>
          )}
          ListEmptyComponent={
            <Text style={styles.empty}>
              No crime news{city ? ` for ${city}` : ""}
              {year !== "Latest" ? ` in ${year}` : ""}.
            </Text>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: spacing.lg },
  header: { fontSize: 18, fontWeight: "700", marginBottom: 8 },
  input: { ...inputStyle, marginBottom: 10 },
  yearRow: { marginBottom: 12, flexGrow: 0 },
  yearChip: {
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: radius.sheet,
    backgroundColor: colors.surfaceMuted,
    marginRight: 8,
  },
  yearChipActive: { backgroundColor: colors.primary },
  yearChipText: { color: colors.textBody, fontWeight: "600" },
  yearChipTextActive: { color: colors.onPrimary },
  card: { borderBottomWidth: 1, borderColor: colors.divider, paddingVertical: 12 },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  title: { fontSize: 15, fontWeight: "600", flexShrink: 1 },
  meta: { color: colors.textSubtle, fontSize: 12, marginTop: 2 },
  summary: { color: colors.textBody, marginTop: 6 },
  empty: { textAlign: "center", color: colors.textFaint, marginTop: 40 },
});
