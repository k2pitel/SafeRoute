import { StyleSheet, View, Text, Switch, TouchableOpacity } from "react-native";

import { colors, spacing, typography } from "../../theme";
import { ChipGroup } from "../../ui";
import { useAuth } from "../auth/AuthContext";
import { useSettings } from "./SettingsContext";

// F6: risk profile + notification settings, plus account and privacy.
// Stored in SettingsContext: the risk profile sets the default route
// ranking (features/routes/rankRoutes), the alert switches control the
// walk monitor's geofence (features/walk/useWalkMonitor).
const RISK_PROFILES = [
  { value: "fast", label: "Fast" },
  { value: "balanced", label: "Balanced" },
  { value: "safest", label: "Safest" },
];

function SettingRow({ label, children }) {
  return (
    <View style={styles.row}>
      <Text>{label}</Text>
      {children}
    </View>
  );
}

function LinkRow({ label }) {
  return (
    <TouchableOpacity style={styles.linkRow}>
      <Text style={styles.link}>{label}</Text>
    </TouchableOpacity>
  );
}

export default function SettingsScreen() {
  const { user, logout } = useAuth();
  const { settings, updateSetting } = useSettings();
  const toggle = (key) => (value) => updateSetting(key, value);

  return (
    <View style={styles.container}>
      <Text style={styles.section}>Account</Text>
      {user ? (
        <SettingRow label={user.email}>
          <TouchableOpacity onPress={logout}>
            <Text style={styles.link}>Log out</Text>
          </TouchableOpacity>
        </SettingRow>
      ) : (
        <Text style={styles.hint}>Not logged in — you'll be asked to log in when you report an incident.</Text>
      )}

      <Text style={styles.section}>Route preference</Text>
      <ChipGroup options={RISK_PROFILES} value={settings.riskProfile} onChange={toggle("riskProfile")} />

      <Text style={styles.section}>Notifications</Text>
      <SettingRow label="Red zone entry alerts">
        <Switch value={settings.zoneAlerts} onValueChange={toggle("zoneAlerts")} />
      </SettingRow>
      <SettingRow label="Time-based safety alerts">
        <Switch value={settings.timeAlerts} onValueChange={toggle("timeAlerts")} />
      </SettingRow>

      <Text style={styles.section}>Emergency</Text>
      <SettingRow label="Share location with emergency contacts">
        <Switch value={settings.shareLocationWithContacts} onValueChange={toggle("shareLocationWithContacts")} />
      </SettingRow>
      <LinkRow label="Manage emergency contacts →" />

      <Text style={styles.section}>Privacy</Text>
      <LinkRow label="How SafeRoute protects your report data →" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: spacing.lg },
  section: { ...typography.sectionLabel, marginTop: spacing.xl, marginBottom: spacing.sm },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderColor: colors.dividerLight,
  },
  linkRow: { paddingVertical: 10 },
  link: { color: colors.primary },
  hint: { color: colors.textMuted, ...typography.caption, paddingVertical: 6 },
});
