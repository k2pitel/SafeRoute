import { useEffect, useState } from "react";
import { StyleSheet, View, Text, FlatList, TouchableOpacity } from "react-native";

import { api } from "../services/api";

// Web build of the Map page. `react-native-maps` has no web target, so on
// web (Metro picks this file over MapScreen.js automatically) we fall back
// to a plain list of incidents instead of a rendered map.
export default function MapScreen() {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);

  useEffect(() => {
    const bbox = [10.15, 56.13, 10.26, 56.19].join(",");
    api.getIncidents(bbox).then(setIncidents).catch(() => setIncidents([]));
  }, []);

  return (
    <View style={styles.container}>
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
        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>{selectedIncident.type}</Text>
          <Text>Date: {new Date(selectedIncident.occurred_at).toLocaleString()}</Text>
          <Text>Info: {selectedIncident.description}</Text>
          <TouchableOpacity onPress={() => setSelectedIncident(null)}>
            <Text style={styles.close}>Close</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  banner: { backgroundColor: "#FFF3CD", padding: 12 },
  bannerText: { color: "#664D03", fontSize: 13 },
  empty: { padding: 16, color: "#666" },
  row: { padding: 16, borderBottomWidth: 1, borderBottomColor: "#eee" },
  rowTitle: { fontWeight: "bold", textTransform: "capitalize" },
  rowSubtitle: { color: "#666", marginTop: 2 },
  infoCard: {
    position: "absolute",
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: "white",
    borderRadius: 12,
    padding: 16,
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  infoTitle: { fontWeight: "bold", fontSize: 16, marginBottom: 4, textTransform: "capitalize" },
  close: { color: "#007AFF", marginTop: 8 },
});
