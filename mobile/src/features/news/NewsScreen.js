import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Linking,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { api } from "../../services/api";
import { radius, spacing, useTheme, useThemedStyles } from "../../theme";
import { StateView } from "../../ui";

// F9: crime-related news, nationwide by default, optionally filtered to a city.
// "Latest" pulls live feeds + recently-archived items; picking a year
// switches to browsing the historical archive instead (see
// backend/app/api/news/backfill.py for how 2020+ got in there).
const YEARS = ["Latest", 2026, 2025, 2024, 2023, 2022, 2021, 2020];

function timeAgo(iso) {
  const then = new Date(iso);
  const minutes = Math.round((Date.now() - then.getTime()) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days} d ago`;
  return then.toLocaleDateString();
}

function NewsCard({ item }) {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  return (
    <TouchableOpacity style={styles.card} activeOpacity={0.75} onPress={() => Linking.openURL(item.url)}>
      <View style={styles.cardTop}>
        <View style={styles.sourceBadge}>
          <Text style={styles.sourceText} numberOfLines={1}>{item.source}</Text>
        </View>
        <Text style={styles.time}>{timeAgo(item.published_at)}</Text>
      </View>
      <Text style={styles.title}>{item.title}</Text>
      {item.summary ? <Text style={styles.summary} numberOfLines={3}>{item.summary}</Text> : null}
      <View style={styles.cardBottom}>
        {item.latitude != null ? (
          <View style={styles.locationPill}>
            <Ionicons name="location" size={12} color={colors.danger} />
            <Text style={styles.locationText}>On the map</Text>
          </View>
        ) : <View />}
        <View style={styles.readMore}>
          <Text style={styles.readMoreText}>Read</Text>
          <Ionicons name="arrow-forward" size={14} color={colors.primary} />
        </View>
      </View>
    </TouchableOpacity>
  );
}

export default function NewsScreen() {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  const [city, setCity] = useState(""); // empty = all of Denmark
  const [year, setYear] = useState("Latest");
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const requestId = useRef(0);

  const load = useCallback((cityFilter, yearFilter, { pull = false } = {}) => {
    // Only the newest request may update the screen: switching year while a
    // slow "Latest" fetch is in flight must not let the old answer win.
    const id = ++requestId.current;
    pull ? setRefreshing(true) : setLoading(true);
    setError(null);
    api
      .getNews(cityFilter || undefined, yearFilter === "Latest" ? undefined : yearFilter)
      .then((items) => id === requestId.current && setNews(items))
      .catch((e) => {
        if (id !== requestId.current) return;
        setNews([]);
        setError(e);
      })
      .finally(() => {
        if (id !== requestId.current) return;
        setLoading(false);
        setRefreshing(false);
      });
  }, []);

  useEffect(() => load(city, year), []); // eslint-disable-line react-hooks/exhaustive-deps

  const selectYear = (y) => {
    setYear(y);
    load(city, y);
  };

  const header = (
    <View>
      <Text style={styles.heading}>Crime news</Text>
      <Text style={styles.subheading}>
        {city ? `Filtered to ${city}` : "All of Denmark"} · {year === "Latest" ? "latest" : year}
      </Text>

      <View style={styles.searchBox}>
        <Ionicons name="search" size={18} color={colors.textFaint} style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          value={city}
          onChangeText={setCity}
          onSubmitEditing={() => load(city, year)}
          placeholder="Filter by city, e.g. Aarhus"
          placeholderTextColor={colors.textFaint}
          returnKeyType="search"
        />
        {city ? (
          <TouchableOpacity onPress={() => { setCity(""); load("", year); }} hitSlop={10}>
            <Ionicons name="close-circle" size={18} color={colors.textFaint} />
          </TouchableOpacity>
        ) : null}
      </View>

      <FlatList
        horizontal
        showsHorizontalScrollIndicator={false}
        data={YEARS}
        keyExtractor={(y) => String(y)}
        style={styles.yearRow}
        contentContainerStyle={styles.yearRowContent}
        renderItem={({ item: y }) => (
          <TouchableOpacity style={[styles.yearChip, y === year && styles.yearChipActive]} onPress={() => selectYear(y)}>
            <Text style={[styles.yearChipText, y === year && styles.yearChipTextActive]}>{y}</Text>
          </TouchableOpacity>
        )}
      />
      {!loading && !error && news.length > 0 ? (
        <Text style={styles.count}>{news.length} articles</Text>
      ) : null}
    </View>
  );

  let empty;
  if (loading) {
    empty = <ActivityIndicator style={styles.spinner} color={colors.primary} />;
  } else if (error) {
    empty = (
      <StateView
        tone="error"
        icon={error.offline ? "cloud-offline-outline" : "alert-circle-outline"}
        title={error.offline ? "Can't reach the server" : "Couldn't load the news"}
        message={error.offline
          ? "The SafeRoute backend or its tunnel isn't answering. Check that start.cmd is still running, then try again."
          : error.message}
        actionLabel="Try again"
        onAction={() => load(city, year)}
      />
    );
  } else {
    empty = (
      <StateView
        icon="newspaper-outline"
        title="No crime news"
        message={`Nothing found${city ? ` for ${city}` : ""}${year !== "Latest" ? ` in ${year}` : ""}.`}
      />
    );
  }

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.content}
      data={loading ? [] : news}
      keyExtractor={(item) => item.url}
      renderItem={({ item }) => <NewsCard item={item} />}
      ListHeaderComponent={header}
      ListEmptyComponent={empty}
      keyboardShouldPersistTaps="handled"
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => load(city, year, { pull: true })}
          tintColor={colors.primary}
          colors={[colors.primary]}
        />
      }
    />
  );
}

const makeStyles = ({ colors, card, inputStyle, typography }) =>
  StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    content: { padding: spacing.lg, paddingBottom: spacing.xxl },
    heading: { ...typography.title, fontSize: 24 },
    subheading: { color: colors.textSubtle, marginTop: 2, marginBottom: spacing.md },

    searchBox: { ...inputStyle, flexDirection: "row", alignItems: "center", paddingVertical: 0, marginBottom: spacing.md },
    searchIcon: { marginRight: spacing.sm },
    searchInput: { flex: 1, paddingVertical: 11, fontSize: 15, color: colors.text },

    yearRow: { flexGrow: 0, marginHorizontal: -spacing.lg, marginBottom: spacing.md },
    yearRowContent: { paddingHorizontal: spacing.lg, gap: spacing.sm },
    yearChip: {
      paddingVertical: 7,
      paddingHorizontal: 16,
      borderRadius: radius.pill,
      backgroundColor: colors.surface,
      borderWidth: 1,
      borderColor: colors.borderLight,
    },
    yearChipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
    yearChipText: { color: colors.textBody, fontWeight: "600" },
    yearChipTextActive: { color: colors.onPrimary },
    count: { ...typography.sectionLabel, marginBottom: spacing.sm },

    card: { ...card, padding: spacing.lg, marginBottom: spacing.md },
    cardTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.sm },
    sourceBadge: {
      backgroundColor: colors.primarySoft,
      borderRadius: radius.pill,
      paddingVertical: 3,
      paddingHorizontal: 10,
      maxWidth: "65%",
    },
    sourceText: { color: colors.primaryDark, fontSize: 12, fontWeight: "700" },
    time: { color: colors.textFaint, fontSize: 12 },
    title: { fontSize: 16, fontWeight: "700", color: colors.text, lineHeight: 22 },
    summary: { color: colors.textMuted, marginTop: 6, lineHeight: 20 },
    cardBottom: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: spacing.md },
    locationPill: {
      flexDirection: "row",
      alignItems: "center",
      gap: 4,
      backgroundColor: colors.dangerSoft,
      borderRadius: radius.pill,
      paddingVertical: 3,
      paddingHorizontal: 8,
    },
    locationText: { color: colors.danger, fontSize: 11, fontWeight: "700" },
    readMore: { flexDirection: "row", alignItems: "center", gap: 4 },
    readMoreText: { color: colors.primary, fontWeight: "700", fontSize: 13 },
    spinner: { marginTop: spacing.xxl },
  });
