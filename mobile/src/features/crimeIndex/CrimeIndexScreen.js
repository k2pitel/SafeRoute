import { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { api } from "../../services/api";
import { radius, spacing, useTheme, useThemedStyles } from "../../theme";
import { StateView } from "../../ui";
import { CountryRanking, EuropeanCityRanking } from "./RankingViews";


// F4 (US-29): city safety overview from real data — the municipality's
// official violent-crime rate (Danmarks Statistik), its national rank and
// recent community reports and news. Picker limited to covered cities.
const QUICK_CITIES = ["København", "Aarhus", "Odense", "Aalborg", "Esbjerg"];

const LABEL_LEVEL = { unsafe: "High", mixed: "Moderate", safe: "Low" };

function ScoreCard({ label, value, suffix, tint, icon }) {
  const styles = useThemedStyles(makeStyles);
  return (
    <View style={[styles.scoreCard, { backgroundColor: tint.bg }]}>
      <Ionicons name={icon} size={18} color={tint.fg} />
      <Text style={[styles.scoreValue, { color: tint.fg }]}>
        {value}
        {suffix ? <Text style={styles.scoreSuffix}>{suffix}</Text> : null}
      </Text>
      <Text style={styles.scoreLabel}>{label}</Text>
    </View>
  );
}

function Fact({ icon, label, value }) {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  return (
    <View style={styles.fact}>
      <Ionicons name={icon} size={16} color={colors.primary} />
      <Text style={styles.factLabel}>{label}</Text>
      <Text style={styles.factValue}>{value}</Text>
    </View>
  );
}

function CityView() {
  const { colors, levelColors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  const [query, setQuery] = useState("Aarhus");
  const [cities, setCities] = useState([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [focused, setFocused] = useState(false);
  const load = (cityName) => {
    setQuery(cityName);
    setFocused(false);
    setLoading(true);
    setError(null);
    api
      .getCrimeIndex(cityName)
      .then(setData)
      .catch((e) => {
        setData(null);
        setError(e);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load(query);
    api.getCrimeIndexCities().then(setCities).catch(() => setCities([]));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const suggestions = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!focused || q.length < 1) return [];
    return cities.filter((c) => c.toLowerCase().startsWith(q)).slice(0, 6);
  }, [cities, query, focused]);

  const ratio = data ? data.rate_per_100k / data.national_rate_per_100k : 1;
  const levelTint = data ? levelColors(LABEL_LEVEL[data.safety_label]) : null;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <View style={styles.searchBox}>
        <Ionicons name="business-outline" size={18} color={colors.textFaint} style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          value={query}
          onChangeText={setQuery}
          onFocus={() => setFocused(true)}
          onSubmitEditing={() => load(query)}
          placeholder="Danish city or municipality"
          placeholderTextColor={colors.textFaint}
          returnKeyType="search"
        />
        <TouchableOpacity onPress={() => load(query)} hitSlop={10}>
          <Ionicons name="arrow-forward-circle" size={24} color={colors.primary} />
        </TouchableOpacity>
      </View>

      {suggestions.length > 0 && (
        <View style={styles.suggestions}>
          {suggestions.map((c) => (
            <TouchableOpacity key={c} style={styles.suggestion} onPress={() => load(c)}>
              <Text style={styles.suggestionText}>{c}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.quickRow} contentContainerStyle={styles.quickContent}>
        {QUICK_CITIES.map((c) => (
          <TouchableOpacity key={c} style={styles.quickChip} onPress={() => load(c)}>
            <Text style={styles.quickText}>{c}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {loading && (
        <View style={styles.loadingBox}>
          <ActivityIndicator color={colors.primary} />
        </View>
      )}

      {!loading && error && (
        <StateView
          tone="error"
          icon={error.offline ? "cloud-offline-outline" : "search-outline"}
          title={error.offline ? "Can't reach the server" : "No data for this city"}
          message={error.offline ? "Check that start.cmd is still running, then try again." : error.message}
          actionLabel={error.offline ? "Try again" : null}
          onAction={() => load(query)}
        />
      )}

      {!loading && data && (
        <>
          <Text style={styles.cityTitle}>
            {data.city}
            {data.municipality.toLowerCase() !== data.city.toLowerCase() ? (
              <Text style={styles.cityMuni}>  ·  {data.municipality} Municipality</Text>
            ) : null}
          </Text>
          <Text style={styles.periodLine}>
            {data.from_year ? `Period ${data.data_period}` : `Latest 12 months (${data.data_period})`}
          </Text>

          <View style={styles.scoreRow}>
            <ScoreCard
              label={`of Danish municipalities have a lower rate`}
              value={`${data.crime_index.toFixed(0)}%`}
              icon="stats-chart-outline"
              tint={levelTint}
            />
            <ScoreCard
              label="Map safety score (same as the map colour)"
              value={(data.safety_index / 10).toFixed(1)}
              suffix=" / 10"
              icon="shield-checkmark-outline"
              tint={levelTint}
            />
          </View>

          <View style={styles.compareCard}>
            <Text style={styles.compareTitle}>Reported violent offences per 100,000 residents per year</Text>
            <View style={styles.compareRow}>
              <Text style={styles.compareName}>{data.municipality}</Text>
              <Text style={[styles.compareValue, { color: levelTint.fg }]}>{data.rate_per_100k.toFixed(0)}</Text>
            </View>
            <View style={styles.track}>
              <View
                style={[styles.fill, { width: `${Math.min(100, (ratio / 2) * 100)}%`, backgroundColor: levelTint.fg }]}
              />
              <View style={styles.nationalMark} />
            </View>
            <View style={styles.compareRow}>
              <Text style={styles.compareHint}>Denmark average</Text>
              <Text style={styles.compareHint}>{data.national_rate_per_100k.toFixed(0)}</Text>
            </View>
            <Text style={styles.explain}>
              Every reported violent offence, incl. minor assaults and threats: a much broader count than homicides, so
              compare it only with other Danish areas. City centres look higher because visitors and nightlife guests
              add offences but don't count as residents.
            </Text>
          </View>

          <View style={styles.factsCard}>
            <Fact
              icon="podium-outline"
              label="Rank in Denmark (1 = highest rate)"
              value={`${data.rank} of ${data.municipalities_ranked}`}
            />
            <Fact icon="people-outline" label="Population" value={data.population.toLocaleString()} />
            <Fact
              icon="alert-circle-outline"
              label={data.from_year ? `Community reports, ${data.data_period}` : "Community reports, 30 days"}
              value={String(data.recent_reports_30d)}
            />
            <Fact
              icon="newspaper-outline"
              label={data.from_year ? `Crime news, ${data.data_period}` : "Crime news, 90 days"}
              value={String(data.recent_news_90d)}
            />
          </View>

          {data.perception ? (
            <View style={styles.compareCard}>
              <Text style={styles.compareTitle}>How it feels at night</Text>
              <View style={styles.compareRow}>
                <Text style={styles.compareName}>Feel safe walking alone at night</Text>
                <Text style={[styles.compareValue, { color: colors.safe }]}>
                  {data.perception.night_safe_percent.toFixed(0)}%
                </Text>
              </View>
              <View style={styles.stack}>
                <View style={[styles.stackPart, { flex: data.perception.night_safe_percent, backgroundColor: colors.safe }]} />
                <View style={[styles.stackPart, { flex: data.perception.night_unsafe_percent, backgroundColor: colors.danger }]} />
                <View
                  style={[
                    styles.stackPart,
                    {
                      flex: Math.max(0, 100 - data.perception.night_safe_percent - data.perception.night_unsafe_percent),
                      backgroundColor: colors.surfaceMuted,
                    },
                  ]}
                />
              </View>
              <Text style={styles.compareHint}>
                {data.perception.night_unsafe_percent.toFixed(0)}% don't
                {data.perception.neighbourhood_night_safe_percent != null
                  ? ` · ${data.perception.neighbourhood_night_safe_percent.toFixed(0)}% feel safe in their own neighbourhood`
                  : ""}
              </Text>
              <Text style={styles.compareHint}>
                #{data.perception.rank} of the European cities surveyed · Eurostat {data.perception.year}
              </Text>
            </View>
          ) : (
            <Text style={styles.noSurvey}>
              {data.municipality} wasn't part of the EU's city survey, so there's no "how safe it feels" figure.
            </Text>
          )}

          {data.country ? (
            <View style={styles.factsCard}>
              <Text style={[styles.compareTitle, styles.countryTitle]}>{data.country.name} in the world</Text>
              <Fact
                icon="globe-outline"
                label="Safer than"
                value={`${Math.round(((data.country.rank - 1) / Math.max(data.country.countries_ranked - 1, 1)) * 100)}% of countries`}
              />
              <Fact
                icon="shield-outline"
                label="Safety Index (higher = safer)"
                value={`${data.country.safety_index.toFixed(0)} / 100`}
              />
              <Fact
                icon="pulse-outline"
                label={`Homicides per 100,000 (${data.country.homicides_year})`}
                value={data.country.homicides_per_100k.toFixed(2)}
              />
              {data.country.crime_in_area_percent != null ? (
                <Fact
                  icon="home-outline"
                  label={`Report crime nearby (EU avg ${data.country.eu_crime_in_area_percent ?? "–"}%)`}
                  value={`${data.country.crime_in_area_percent}%`}
                />
              ) : null}
            </View>
          ) : null}

          <View style={styles.aiBox}>
            <View style={styles.aiHeader}>
              <Ionicons name="document-text-outline" size={16} color={colors.primary} />
              <Text style={styles.aiTitle}>Summary</Text>
            </View>
            <Text style={styles.aiText}>{data.summary}</Text>
          </View>

          <Text style={styles.footer}>
            Danmarks Statistik{data.data_period ? `, ${data.data_period}` : ""} · Eurostat · World Bank
            {data.last_updated ? ` · fetched ${new Date(data.last_updated).toLocaleDateString()}` : ""}
          </Text>
        </>
      )}
    </ScrollView>
  );
}

const TABS = [
  { key: "city", label: "City" },
  { key: "countries", label: "Countries" },
  { key: "cities", label: "EU cities" },
];

// F4 + free country/city indices (Eurostat, World Bank) in three tabs.
export default function CrimeIndexScreen() {
  const styles = useThemedStyles(makeStyles);
  const [tab, setTab] = useState("city");
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.heading}>Safety index</Text>
        <View style={styles.segment}>
          {TABS.map((t) => (
            <TouchableOpacity
              key={t.key}
              style={[styles.segmentItem, tab === t.key && styles.segmentItemActive]}
              onPress={() => setTab(t.key)}
            >
              <Text style={[styles.segmentText, tab === t.key && styles.segmentTextActive]}>{t.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
      {tab === "city" && <CityView />}
      {tab === "countries" && <CountryRanking />}
      {tab === "cities" && <EuropeanCityRanking />}
    </View>
  );
}

const makeStyles = ({ colors, card, inputStyle, typography, elevation }) =>
  StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    content: { padding: spacing.lg, paddingBottom: spacing.xxl },
    heading: { ...typography.title, fontSize: 24, marginBottom: spacing.md },
    header: { paddingHorizontal: spacing.lg, paddingTop: spacing.lg },
    segment: { flexDirection: "row", backgroundColor: colors.surfaceMuted, borderRadius: radius.md, padding: 3 },
    segmentItem: { flex: 1, paddingVertical: 8, borderRadius: radius.sm, alignItems: "center" },
    segmentItemActive: { backgroundColor: colors.surface, ...elevation, elevation: 2, shadowOpacity: 0.08 },
    segmentText: { color: colors.textMuted, fontWeight: "600" },
    segmentTextActive: { color: colors.primary, fontWeight: "700" },
    stack: { flexDirection: "row", height: 10, borderRadius: 5, overflow: "hidden", marginVertical: 8 },
    stackPart: { height: 10 },
    explain: { color: colors.textSubtle, fontSize: 12, lineHeight: 17, marginTop: spacing.sm },
    loadingBox: { alignItems: "center", gap: spacing.sm, marginTop: spacing.xxl },
    loadingText: { color: colors.textSubtle, fontSize: 13 },
    periodLine: { color: colors.textSubtle, fontSize: 13, marginTop: -spacing.sm, marginBottom: spacing.md },
    noSurvey: { color: colors.textSubtle, fontSize: 12, marginBottom: spacing.md, fontStyle: "italic" },
    countryTitle: { marginTop: spacing.md, marginBottom: 0 },

    searchBox: { ...inputStyle, flexDirection: "row", alignItems: "center", paddingVertical: 0 },
    searchIcon: { marginRight: spacing.sm },
    searchInput: { flex: 1, paddingVertical: 11, fontSize: 15, color: colors.text },
    suggestions: { ...card, ...elevation, marginTop: 4, paddingVertical: 4 },
    suggestion: { paddingVertical: 10, paddingHorizontal: spacing.lg },
    suggestionText: { color: colors.text, fontWeight: "500" },
    quickRow: { flexGrow: 0, marginHorizontal: -spacing.lg, marginTop: spacing.md, marginBottom: spacing.sm },
    quickContent: { paddingHorizontal: spacing.lg, gap: spacing.sm },
    quickChip: {
      paddingVertical: 6,
      paddingHorizontal: 14,
      borderRadius: radius.pill,
      backgroundColor: colors.surface,
      borderWidth: 1,
      borderColor: colors.borderLight,
    },
    quickText: { color: colors.textBody, fontWeight: "600" },
    spinner: { marginTop: spacing.xxl },

    cityTitle: { ...typography.title, marginTop: spacing.md, marginBottom: spacing.md },
    cityMuni: { fontSize: 14, fontWeight: "500", color: colors.textSubtle },

    scoreRow: { flexDirection: "row", gap: spacing.md, marginBottom: spacing.md },
    scoreCard: { flex: 1, borderRadius: radius.lg, padding: spacing.lg },
    scoreValue: { fontSize: 32, fontWeight: "800", marginTop: spacing.sm },
    scoreSuffix: { fontSize: 14, fontWeight: "600" },
    scoreLabel: { color: colors.textMuted, fontWeight: "600", fontSize: 12, lineHeight: 16, marginTop: 4 },

    compareCard: { ...card, padding: spacing.lg, marginBottom: spacing.md },
    compareTitle: { ...typography.sectionLabel, marginBottom: spacing.sm },
    compareRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "baseline" },
    compareName: { color: colors.text, fontWeight: "600" },
    compareValue: { fontSize: 20, fontWeight: "800" },
    compareHint: { color: colors.textSubtle, fontSize: 12 },
    track: { height: 8, borderRadius: 4, backgroundColor: colors.surfaceMuted, marginVertical: 8, overflow: "hidden" },
    fill: { height: 8, borderRadius: 4 },
    // The national average sits at the middle of the bar (ratio 1 = 50 %).
    nationalMark: { position: "absolute", left: "50%", top: 0, bottom: 0, width: 2, backgroundColor: colors.text },

    factsCard: { ...card, paddingHorizontal: spacing.lg, paddingVertical: spacing.xs, marginBottom: spacing.md },
    fact: {
      flexDirection: "row",
      alignItems: "center",
      gap: spacing.sm,
      paddingVertical: 10,
      borderBottomWidth: 1,
      borderColor: colors.dividerLight,
    },
    factLabel: { flex: 1, color: colors.textBody },
    factValue: { color: colors.text, fontWeight: "700" },

    aiBox: { ...card, padding: spacing.lg, borderLeftWidth: 4, borderLeftColor: colors.primary },
    aiHeader: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 6 },
    aiTitle: { fontWeight: "700", color: colors.primary },
    aiText: { color: colors.textBody, lineHeight: 21 },

    footer: { color: colors.textFaint, fontSize: 12, marginTop: spacing.lg, textAlign: "center" },
  });
