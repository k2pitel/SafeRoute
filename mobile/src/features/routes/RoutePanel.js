import { useEffect, useState } from "react";
import { StyleSheet, View, Text, TouchableOpacity, ScrollView } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { api } from "../../services/api";
import { getCurrentCoordinates } from "../../services/location";
import { colors, radius } from "../../theme";
import { ChipGroup } from "../../ui";
import { useSettings } from "../settings/SettingsContext";
import { useActiveRoute } from "./ActiveRouteContext";
import PlaceSearchInput from "./PlaceSearchInput";
import { SORT_OPTIONS, rankRoutes, sortForProfile } from "./rankRoutes";

// UC1 (F1): compact From/To route picker that sits above the map (DSB-app style)
// instead of living on its own tab. Collapsed by default to a single bar;
// tapping it opens the search fields + route list, and picking an option
// collapses it again — the route itself is drawn by MapScreen, which reads
// it straight off ActiveRouteContext.
const NO_ROUTE_MESSAGE = "No route could be found — try adjusting your start or destination.";

export default function RoutePanel() {
  const { activeRoute, setActiveRoute } = useActiveRoute();
  const { settings } = useSettings();

  const [expanded, setExpanded] = useState(false);
  const [origin, setOrigin] = useState(null);
  const [destination, setDestination] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [sortBy, setSortBy] = useState(sortForProfile(settings.riskProfile));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [locating, setLocating] = useState(false);
  const [myLocation, setMyLocation] = useState(null);

  // F6: the risk profile decides the default ranking.
  useEffect(() => setSortBy(sortForProfile(settings.riskProfile)), [settings.riskProfile]);

  // Bias place search towards the user, but only if permission was already
  // granted — don't prompt just for opening the panel.
  useEffect(() => {
    getCurrentCoordinates({ ask: false }).then((coords) => coords && setMyLocation(coords));
  }, []);

  const useMyLocation = async () => {
    setLocating(true);
    try {
      const coords = await getCurrentCoordinates();
      if (!coords) {
        // UC1 extension 2a: no permission -> search the start point instead.
        setError("Location permission is off — search for your start point instead.");
        return;
      }
      setError(null);
      setMyLocation(coords);
      setOrigin({ ...coords, label: "My location" });
    } finally {
      setLocating(false);
    }
  };

  const search = async () => {
    if (!origin || !destination) return;
    setLoading(true);
    setError(null);
    try {
      const from = `${origin.latitude},${origin.longitude}`;
      const to = `${destination.latitude},${destination.longitude}`;
      const results = await api.getRoutes(from, to);
      setRoutes(results);
      if (results.length === 0) setError(NO_ROUTE_MESSAGE);
    } catch (e) {
      // UC1 extension 4a: tell the user and let them adjust start/destination.
      setRoutes([]);
      setError(`${NO_ROUTE_MESSAGE} (${e.message})`);
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

  const sorted = rankRoutes(routes, sortBy);

  if (!expanded) {
    return (
      <TouchableOpacity style={styles.collapsedBar} onPress={() => setExpanded(true)}>
        {activeRoute && (
          <Text style={styles.collapsedText} numberOfLines={1}>
            {`${Math.round(activeRoute.option.duration_minutes)} min · Safety: ${activeRoute.option.safety_label} (${activeRoute.option.safety_score.toFixed(1)}/10)`}
          </Text>
        )}
        <Ionicons name="chevron-down" size={20} color={colors.textMuted} />
      </TouchableOpacity>
    );
  }

  return (
    <View style={styles.panel}>
      <TouchableOpacity style={styles.header} onPress={() => setExpanded(false)}>
        <Ionicons name="chevron-up" size={20} color={colors.textMuted} />
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
            <Ionicons name="locate" size={18} color={colors.primary} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.sideButton}
            onPress={swapOriginAndDestination}
            disabled={!origin && !destination}
          >
            <Ionicons name="swap-vertical" size={18} color={origin || destination ? colors.primary : colors.border} />
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

      {error && <Text style={styles.error}>{error}</Text>}

      {routes.length > 0 && (
        <>
          <ChipGroup options={SORT_OPTIONS} value={sortBy} onChange={setSortBy} style={styles.sortRow} />

          <ScrollView style={styles.results} nestedScrollEnabled>
            {sorted.map((item, i) => (
              <TouchableOpacity key={i} style={styles.routeCard} onPress={() => pickRoute(item)}>
                <Text style={styles.duration}>{Math.round(item.duration_minutes)} min</Text>
                <Text style={styles.safety}>
                  Safety: {item.safety_label} ({item.safety_score.toFixed(1)}/10)
                </Text>
                {/* NF8: every score comes with its explanation */}
                <Text style={styles.explanation}>{item.explanation}</Text>
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
    backgroundColor: colors.surface,
    paddingVertical: 8,
    paddingHorizontal: 14,
    gap: 4,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  collapsedText: { color: colors.textStrong, fontSize: 13, fontWeight: "500" },
  panel: {
    backgroundColor: colors.surface,
    paddingHorizontal: 14,
    paddingTop: 10,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
    maxHeight: 420,
  },
  header: { alignItems: "center", justifyContent: "center", paddingVertical: 2, marginBottom: 6 },
  fieldsRow: { flexDirection: "row", alignItems: "stretch" },
  fieldsColumn: { flex: 1 },
  sideButtons: { justifyContent: "space-between", marginLeft: 8 },
  sideButton: { padding: 6 },
  button: { backgroundColor: colors.primary, borderRadius: radius.sm, padding: 10, alignItems: "center", marginTop: 10 },
  buttonDisabled: { backgroundColor: colors.primaryDisabled },
  buttonText: { color: colors.onPrimary, fontWeight: "600", fontSize: 13 },
  sortRow: { marginTop: 10, marginBottom: 6 },
  error: { color: colors.danger, fontSize: 12, marginTop: 8 },
  explanation: { color: colors.textMuted, marginTop: 4, fontSize: 11 },
  results: { maxHeight: 220 },
  routeCard: { borderWidth: 1, borderColor: colors.divider, borderRadius: radius.md, padding: 10, marginBottom: 6 },
  duration: { fontSize: 15, fontWeight: "700" },
  safety: { color: colors.textBody, marginTop: 2, fontSize: 12 },
});
