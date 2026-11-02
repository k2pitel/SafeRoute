import { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, FlatList, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { api } from "../../services/api";
import { radius, spacing, useTheme, useThemedStyles } from "../../theme";
import { StateView } from "../../ui";

// Numbeo-style rankings built from free official data (backend
// api/crime_index/world.py): countries by Crime/Safety Index, European
// cities by how safe residents feel walking alone at night.

const REGIONS = [
  { value: null, label: "All" },
  { value: "Europe & Central Asia", label: "Europe" },
  { value: "North America", label: "N. America" },
  { value: "Latin America & Caribbean", label: "Latin America" },
  { value: "East Asia & Pacific", label: "Asia-Pacific" },
  { value: "Sub-Saharan Africa", label: "Africa" },
  { value: "Middle East, North Africa, Afghanistan & Pakistan", label: "Middle East" },
  { value: "South Asia", label: "South Asia" },
];

const HOME = ["DK", "DE", "US"]; // the project's three countries, highlighted

function tintFor(levelColors, crimeIndex) {
  return levelColors(crimeIndex >= 60 ? "High" : crimeIndex >= 40 ? "Moderate" : "Low");
}

function useRanking(loader) {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const load = () => {
    setRows(null);
    setError(null);
    loader().then(setRows).catch(setError);
  };
  useEffect(load, []); // eslint-disable-line react-hooks/exhaustive-deps
  return { rows, error, reload: load };
}

function Loading({ rows, error, reload }) {
  const { colors } = useTheme();
  if (error) {
    return (
      <StateView
        tone="error"
        icon={error.offline ? "cloud-offline-outline" : "alert-circle-outline"}
        title={error.offline ? "Can't reach the server" : "Couldn't load the ranking"}
        message={error.message}
        actionLabel="Try again"
        onAction={reload}
      />
    );
  }
  if (!rows) return <ActivityIndicator style={{ marginTop: spacing.xxl }} color={colors.primary} />;
  return null;
}

function SearchBox({ value, onChange, placeholder }) {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  return (
    <View style={styles.searchBox}>
      <Ionicons name="search" size={18} color={colors.textFaint} />
      <TextInput
        style={styles.searchInput}
        value={value}
        onChangeText={onChange}
        placeholder={placeholder}
        placeholderTextColor={colors.textFaint}
      />
    </View>
  );
}

export function CountryRanking() {
  const { colors, levelColors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  const state = useRanking(api.getCountryRanking);
  const [region, setRegion] = useState(null);
  const [query, setQuery] = useState("");

  const rows = useMemo(() => {
    let list = state.rows || [];
    if (region) list = list.filter((r) => r.region === region);
    const q = query.trim().toLowerCase();
    if (q) list = list.filter((r) => r.name.toLowerCase().includes(q));
    return list;
  }, [state.rows, region, query]);

  const header = (
    <View>
      <Text style={styles.intro}>
        Crime Index 0–100: how a country ranks on homicides per 100,000 and, in Europe, on the share of people who
        report crime or vandalism nearby. Safety Index = 100 − Crime Index.
      </Text>
      <SearchBox value={query} onChange={setQuery} placeholder="Find a country" />
      <FlatList
        horizontal
        data={REGIONS}
        keyExtractor={(r) => r.label}
        showsHorizontalScrollIndicator={false}
        style={styles.chipRow}
        contentContainerStyle={styles.chipRowContent}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.chip, item.value === region && styles.chipActive]}
            onPress={() => setRegion(item.value)}
          >
            <Text style={[styles.chipText, item.value === region && styles.chipTextActive]}>{item.label}</Text>
          </TouchableOpacity>
        )}
      />
      <View style={styles.tableHead}>
        <Text style={[styles.th, styles.colRank]}>#</Text>
        <Text style={[styles.th, styles.colName]}>Country</Text>
        <Text style={[styles.th, styles.colNum]}>Crime</Text>
        <Text style={[styles.th, styles.colNum]}>Safety</Text>
      </View>
    </View>
  );

  if (!state.rows) return <Loading {...state} />;

  return (
    <FlatList
      data={rows}
      keyExtractor={(r) => r.iso2}
      ListHeaderComponent={header}
      contentContainerStyle={styles.listContent}
      keyboardShouldPersistTaps="handled"
      renderItem={({ item }) => {
        const tint = tintFor(levelColors, item.crime_index);
        const home = HOME.includes(item.iso2);
        return (
          <View style={[styles.row, home && styles.rowHome]}>
            <Text style={[styles.rank, styles.colRank]}>{item.rank}</Text>
            <View style={styles.colName}>
              <Text style={styles.name} numberOfLines={1}>{item.name}</Text>
              <Text style={styles.sub} numberOfLines={1}>
                {item.homicides_per_100k} homicides/100k ({item.homicides_year})
                {item.crime_in_area_percent != null ? ` · ${item.crime_in_area_percent}% crime nearby` : ""}
              </Text>
            </View>
            <View style={[styles.colNum, styles.badge, { backgroundColor: tint.bg }]}>
              <Text style={[styles.badgeText, { color: tint.fg }]}>{item.crime_index.toFixed(0)}</Text>
            </View>
            <Text style={[styles.colNum, styles.safety]}>{item.safety_index.toFixed(0)}</Text>
          </View>
        );
      }}
      ListFooterComponent={
        <Text style={styles.source}>
          Sources: World Bank (UNODC homicides, CC BY 4.0); Eurostat EU-SILC ilc_mddw03. Rank 1 = most crime.
        </Text>
      }
      ListEmptyComponent={<Text style={[styles.sub, { textAlign: "center", color: colors.textFaint }]}>No match.</Text>}
    />
  );
}

export function EuropeanCityRanking() {
  const { colors, levelColors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  const state = useRanking(api.getEuropeanCityRanking);
  const [query, setQuery] = useState("");

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = state.rows || [];
    return q ? list.filter((r) => r.name.toLowerCase().includes(q) || r.country.toLowerCase().includes(q)) : list;
  }, [state.rows, query]);

  if (!state.rows) return <Loading {...state} />;

  return (
    <FlatList
      data={rows}
      keyExtractor={(r) => r.code}
      contentContainerStyle={styles.listContent}
      keyboardShouldPersistTaps="handled"
      ListHeaderComponent={
        <View>
          <Text style={styles.intro}>
            Share of residents who agree "I feel safe walking alone at night in my city", from the EU's survey of{" "}
            {state.rows.length} European cities.
          </Text>
          <SearchBox value={query} onChange={setQuery} placeholder="Find a city or country" />
        </View>
      }
      renderItem={({ item }) => {
        const pct = item.night_safe_percent;
        const tint = levelColors(pct >= 75 ? "Low" : pct >= 60 ? "Moderate" : "High");
        const home = HOME.includes(item.country_iso2);
        return (
          <View style={[styles.cityRow, home && styles.rowHome]}>
            <View style={styles.cityTop}>
              <Text style={[styles.rank, styles.colRank]}>{item.rank}</Text>
              <View style={styles.colName}>
                <Text style={styles.name} numberOfLines={1}>{item.name}</Text>
                <Text style={styles.sub}>
                  {item.country} · {item.year}
                </Text>
              </View>
              <Text style={[styles.pct, { color: tint.fg }]}>{pct.toFixed(0)}%</Text>
            </View>
            <View style={styles.track}>
              <View style={[styles.fill, { width: `${pct}%`, backgroundColor: tint.fg }]} />
            </View>
          </View>
        );
      }}
      ListFooterComponent={
        <Text style={styles.source}>Source: Eurostat, urb_percep (Perception survey on quality of life in European cities).</Text>
      }
      ListEmptyComponent={<Text style={[styles.sub, { textAlign: "center", color: colors.textFaint }]}>No match.</Text>}
    />
  );
}

const makeStyles = ({ colors, inputStyle }) =>
  StyleSheet.create({
    listContent: { padding: spacing.lg, paddingBottom: spacing.xxl },
    intro: { color: colors.textMuted, lineHeight: 20, marginBottom: spacing.md },
    searchBox: { ...inputStyle, flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingVertical: 0 },
    searchInput: { flex: 1, paddingVertical: 10, fontSize: 15, color: colors.text },
    chipRow: { flexGrow: 0, marginHorizontal: -spacing.lg, marginTop: spacing.md },
    chipRowContent: { paddingHorizontal: spacing.lg, gap: spacing.sm },
    chip: {
      paddingVertical: 6,
      paddingHorizontal: 12,
      borderRadius: radius.pill,
      backgroundColor: colors.surface,
      borderWidth: 1,
      borderColor: colors.borderLight,
    },
    chipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
    chipText: { color: colors.textBody, fontWeight: "600", fontSize: 13 },
    chipTextActive: { color: colors.onPrimary },
    tableHead: {
      flexDirection: "row",
      alignItems: "center",
      paddingVertical: spacing.sm,
      marginTop: spacing.md,
      borderBottomWidth: 1,
      borderColor: colors.divider,
    },
    th: { fontSize: 11, fontWeight: "700", letterSpacing: 0.6, color: colors.textSubtle, textTransform: "uppercase" },
    row: {
      flexDirection: "row",
      alignItems: "center",
      paddingVertical: 10,
      borderBottomWidth: 1,
      borderColor: colors.dividerLight,
    },
    rowHome: { backgroundColor: colors.primarySoft, marginHorizontal: -spacing.sm, paddingHorizontal: spacing.sm, borderRadius: radius.sm },
    colRank: { width: 34 },
    colName: { flex: 1, paddingRight: spacing.sm },
    colNum: { width: 52, alignItems: "center", textAlign: "center" },
    rank: { color: colors.textSubtle, fontWeight: "700", fontVariant: ["tabular-nums"] },
    name: { color: colors.text, fontWeight: "600" },
    sub: { color: colors.textSubtle, fontSize: 11, marginTop: 1 },
    badge: { borderRadius: radius.pill, paddingVertical: 3 },
    badgeText: { fontWeight: "800", fontVariant: ["tabular-nums"] },
    safety: { color: colors.textBody, fontWeight: "600", fontVariant: ["tabular-nums"] },
    cityRow: { paddingVertical: 10, borderBottomWidth: 1, borderColor: colors.dividerLight },
    cityTop: { flexDirection: "row", alignItems: "center" },
    pct: { fontSize: 18, fontWeight: "800", fontVariant: ["tabular-nums"] },
    track: { height: 5, borderRadius: 3, backgroundColor: colors.surfaceMuted, marginTop: 6, marginLeft: 34, overflow: "hidden" },
    fill: { height: 5, borderRadius: 3 },
    source: { color: colors.textFaint, fontSize: 11, textAlign: "center", marginTop: spacing.lg },
  });
