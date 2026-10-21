import { useEffect, useState } from "react";
import { StyleSheet, View, Text, FlatList, TouchableOpacity } from "react-native";

import { api } from "../../services/api";
import { colors, spacing, typography } from "../../theme";
import RoutePanel from "../routes/RoutePanel";
import { IncidentInfoCard } from "./MarkerInfoCards";

// Aarhus city centre — the web fallback has no map to pan, so it lists one fixed area.
const WEB_BBOX = [10.15, 56.13, 10.26, 56.19].join(",");

// Web build of the Map page. `react-native-maps` has no web target, so on
// web (Metro picks this file over MapScreen.js automatically) we fall back
// to a plain list of incidents instead of a rendered map.
export default function MapScreen() {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);

  useEffect(() => {
    api.getIncidents(WEB_BBOX).then(setIncidents).catch(() => setIncidents([]));
  }, []);

  return (
    <View style={styles.container}>
      <RoutePanel />

      <View style={styles.banner}>
        <Text style={styles.bannerText}>
          Map view isn't available in the browser (react-native-maps is
          native-only). Open this app in Expo Go on your phone to see the
          real map. Showing nearby incidents as a list below.
        </Text>
      </View>

      <FlatList
        data={incidents}
        keyExtractor={(item) => String(item.id)}
        ListEmptyComponent={<Text style={styles.empty}>No incidents to show.</Text>}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.row} onPress={() => setSelectedIncident(item)}>
            <Text style={styles.rowTitle}>{item.type}</Text>
            <Text style={styles.rowSubtitle}>{new Date(item.occurred_at).toLocaleString()}</Text>
          </TouchableOpacity>
        )}
      />

      {selectedIncident && (
        <IncidentInfoCard incident={selectedIncident} onClose={() => setSelectedIncident(null)} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  banner: { backgroundColor: colors.warningSurface, padding: spacing.md },
  bannerText: { color: colors.warningText, ...typography.caption },
  empty: { padding: spacing.lg, color: colors.textMuted },
  row: { padding: spacing.lg, borderBottomWidth: 1, borderBottomColor: colors.divider },
  rowTitle: { fontWeight: "bold", textTransform: "capitalize" },
  rowSubtitle: { color: colors.textMuted, marginTop: 2 },
});
