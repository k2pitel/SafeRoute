import { useState } from "react";
import { StyleSheet, View, Text, Switch, TouchableOpacity } from "react-native";

// README > Mobile App — Pages > 5. Settings
// Risk tolerance, notification toggles, emergency contacts, privacy controls.
const RISK_PROFILES = ["fast", "balanced", "safest"];

export default function SettingsScreen() {
  const [riskProfile, setRiskProfile] = useState("balanced");
  const [redZoneAlerts, setRedZoneAlerts] = useState(true);
  const [timeBasedAlerts, setTimeBasedAlerts] = useState(true);
  const [shareLocationWithContacts, setShareLocationWithContacts] = useState(false);

  return (
    <View style={styles.container}>
      <Text style={styles.section}>Route preference</Text>
      <View style={styles.riskRow}>
        {RISK_PROFILES.map((profile) => (
          <TouchableOpacity
            key={profile}
            style={[styles.riskPill, riskProfile === profile && styles.riskPillActive]}
            onPress={() => setRiskProfile(profile)}
          >
            <Text style={riskProfile === profile ? styles.riskTextActive : styles.riskText}>
              {profile}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.section}>Notifications</Text>
      <View style={styles.row}>
        <Text>Red zone entry alerts</Text>
        <Switch value={redZoneAlerts} onValueChange={setRedZoneAlerts} />
      </View>
      <View style={styles.row}>
        <Text>Time-based safety alerts</Text>
        <Switch value={timeBasedAlerts} onValueChange={setTimeBasedAlerts} />
      </View>

      <Text style={styles.section}>Emergency</Text>
      <View style={styles.row}>
        <Text>Share location with emergency contacts</Text>
        <Switch value={shareLocationWithContacts} onValueChange={setShareLocationWithContacts} />
      </View>
      <TouchableOpacity style={styles.linkRow}>
        <Text style={styles.link}>Manage emergency contacts →</Text>
      </TouchableOpacity>

      <Text style={styles.section}>Privacy</Text>
      <TouchableOpacity style={styles.linkRow}>
        <Text style={styles.link}>How SafeRoute protects your report data →</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  section: { fontSize: 13, color: "#888", textTransform: "uppercase", marginTop: 20, marginBottom: 8 },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderColor: "#f0f0f0",
  },
  riskRow: { flexDirection: "row", gap: 8 },
  riskPill: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 20,
    paddingVertical: 6,
    paddingHorizontal: 14,
  },
  riskPillActive: { backgroundColor: "#007AFF", borderColor: "#007AFF" },
  riskText: { color: "#333", textTransform: "capitalize" },
  riskTextActive: { color: "white", textTransform: "capitalize" },
  linkRow: { paddingVertical: 10 },
  link: { color: "#007AFF" },
});
