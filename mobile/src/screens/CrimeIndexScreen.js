import { useEffect, useState } from "react";
import { StyleSheet, View, Text, TextInput, ScrollView, ActivityIndicator } from "react-native";

import { api } from "../services/api";

// README > Mobile App — Pages > 4. Crime Index Page
// Numbeo-style breakdown + AI-generated summary for a city.
const METRIC_LABELS = {
  level_of_crime: "Level of crime",
  crime_increasing_5y: "Crime increasing (5y)",
  worries_home_broken: "Worries home broken into",
  worries_mugged: "Worries being mugged",
  worries_car_stolen: "Worries car stolen",
  problem_drugs: "Problem: drugs",
  problem_property_crime: "Problem: property crime",
  problem_violent_crime: "Problem: violent crime",
  safety_walking_daylight: "Safety walking (daylight)",
  safety_walking_night: "Safety walking (night)",
};

function levelFor(value) {
  if (value >= 60) return "High";
  if (value >= 40) return "Moderate";
  return "Low";
}

export default function CrimeIndexScreen() {
  const [city, setCity] = useState("Aarhus, Denmark");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = (cityName) => {
    setLoading(true);
    api
      .getCrimeIndex(cityName)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => load(city), []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <ScrollView style={styles.container}>
      <TextInput
        style={styles.input}
        value={city}
        onChangeText={setCity}
        onSubmitEditing={() => load(city)}
        placeholder="City, Country"
      />

      {loading && <ActivityIndicator style={{ marginTop: 20 }} />}

      {data && (
        <>
          <View style={styles.scoreRow}>
            <View style={styles.scoreBox}>
              <Text style={styles.scoreValue}>{data.crime_index.toFixed(1)}</Text>
              <Text style={styles.scoreLabel}>Crime Index</Text>
            </View>
            <View style={styles.scoreBox}>
              <Text style={styles.scoreValue}>{data.safety_index.toFixed(1)}</Text>
              <Text style={styles.scoreLabel}>Safety Index</Text>
            </View>
          </View>

          {Object.entries(data.metrics).map(([key, value]) => (
            <View key={key} style={styles.metricRow}>
              <Text style={styles.metricLabel}>{METRIC_LABELS[key] || key}</Text>
              <Text style={styles.metricValue}>
                {value.toFixed(2)} · {levelFor(value)}
              </Text>
            </View>
          ))}

          <View style={styles.aiBox}>
            <Text style={styles.aiTitle}>AI Summary</Text>
            <Text>{data.ai_summary}</Text>
          </View>

          <Text style={styles.footer}>
            Based on {data.contributors} contributors · Last update{" "}
            {new Date(data.last_updated).toLocaleDateString()}
          </Text>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  input: { borderWidth: 1, borderColor: "#ccc", borderRadius: 8, padding: 10, marginBottom: 16 },
  scoreRow: { flexDirection: "row", justifyContent: "space-around", marginBottom: 20 },
  scoreBox: { alignItems: "center" },
  scoreValue: { fontSize: 28, fontWeight: "800" },
  scoreLabel: { color: "#666" },
  metricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderColor: "#f0f0f0",
  },
  metricLabel: { color: "#333", flex: 1 },
  metricValue: { color: "#666" },
  aiBox: { backgroundColor: "#f5f7ff", borderRadius: 10, padding: 14, marginTop: 20 },
  aiTitle: { fontWeight: "700", marginBottom: 6 },
  footer: { color: "#999", fontSize: 12, marginVertical: 16, textAlign: "center" },
});
