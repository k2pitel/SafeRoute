import { useState } from "react";
import { Alert, ScrollView, Share, StyleSheet, Switch, Text, TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { radius, spacing, useTheme, useThemedStyles } from "../../theme";
import { ChipGroup } from "../../ui";
import { api } from "../../services/api";
import { useAuth } from "../auth/AuthContext";
import DataStatusSheet from "./DataStatusSheet";
import EmergencyContactsSheet from "./EmergencyContactsSheet";
import MyReportsSheet from "./MyReportsSheet";
import PrivacySheet from "./PrivacySheet";
import { useSettings } from "./SettingsContext";

// F6: risk profile + notification settings, plus account and privacy.
// Stored in SettingsContext: the risk profile sets the default route
// ranking (features/routes/rankRoutes), the alert switches control the
// walk monitor's geofence (features/walk/useWalkMonitor).
const APPEARANCES = [
  { value: "system", label: "System" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
];

const RISK_PROFILES = [
  { value: "fast", label: "Fast" },
  { value: "balanced", label: "Balanced" },
  { value: "safest", label: "Safest" },
];

function Section({ title, children }) {
  const styles = useThemedStyles(makeStyles);
  return (
    <>
      <Text style={styles.section}>{title}</Text>
      <View style={styles.group}>{children}</View>
    </>
  );
}

function RowIcon({ name, color, bg }) {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  return (
    <View style={[styles.rowIcon, { backgroundColor: bg || colors.primarySoft }]}>
      <Ionicons name={name} size={16} color={color || colors.primary} />
    </View>
  );
}

function SettingRow({ icon, label, last, children }) {
  const styles = useThemedStyles(makeStyles);
  return (
    <View style={[styles.row, !last && styles.rowDivider]}>
      {icon}
      <Text style={styles.rowLabel}>{label}</Text>
      {children}
    </View>
  );
}

function LinkRow({ icon, label, last, onPress, danger }) {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  return (
    <TouchableOpacity style={[styles.row, !last && styles.rowDivider]} onPress={onPress}>
      {icon}
      <Text style={[styles.rowLabel, danger && { color: colors.danger }]}>{label}</Text>
      <Ionicons name="chevron-forward" size={18} color={colors.textFaint} />
    </TouchableOpacity>
  );
}

export default function SettingsScreen() {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  const { user, logout } = useAuth();
  const { settings, updateSetting } = useSettings();
  const toggle = (key) => (value) => updateSetting(key, value);
  const switchColors = { false: colors.border, true: colors.primary };
  const [sheet, setSheet] = useState(null); // 'reports' | 'privacy' | 'contacts' | 'data'
  const closeSheet = () => setSheet(null);

  // US-59 (GDPR art. 15/20): everything stored about the user, handed to
  // the phone's share sheet (save to Files, mail it, ...).
  const exportData = async () => {
    try {
      const data = await api.exportMyData();
      await Share.share({ title: "My SafeRoute data", message: JSON.stringify(data, null, 2) });
    } catch (e) {
      Alert.alert("Export failed", e.message);
    }
  };

  // US-59 (GDPR art. 17)
  const deleteAccount = () =>
    Alert.alert(
      "Delete account?",
      "This permanently deletes your account, all your reports and your confirmations. It can't be undone.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await api.deleteAccount();
              await logout();
              Alert.alert("Account deleted", "Your account and reports have been removed.");
            } catch (e) {
              Alert.alert("Could not delete account", e.message);
            }
          },
        },
      ]
    );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Section title="Account">
        {user ? (
          <>
            <SettingRow icon={<RowIcon name="person" />} label={user.email}>
              <TouchableOpacity onPress={logout}>
                <Text style={styles.logout}>Log out</Text>
              </TouchableOpacity>
            </SettingRow>
            <LinkRow icon={<RowIcon name="document-text" />} label="My reports" onPress={() => setSheet("reports")} />
            <LinkRow icon={<RowIcon name="download" />} label="Export my data" onPress={exportData} />
            <LinkRow
              icon={<RowIcon name="trash" color={colors.danger} bg={colors.dangerSoft} />}
              label="Delete account"
              onPress={deleteAccount}
              danger
              last
            />
          </>
        ) : (
          <View style={styles.row}>
            <RowIcon name="person-outline" color={colors.textSubtle} bg={colors.surfaceMuted} />
            <Text style={styles.hint}>Not logged in. You'll be asked to log in when you report an incident.</Text>
          </View>
        )}
      </Section>

      <Section title="Appearance">
        <View style={styles.chipsWrap}>
          <ChipGroup options={APPEARANCES} value={settings.appearance} onChange={toggle("appearance")} />
          <Text style={styles.chipHint}>"System" follows your phone's light/dark setting.</Text>
        </View>
      </Section>

      <Section title="Route preference">
        <View style={styles.chipsWrap}>
          <ChipGroup options={RISK_PROFILES} value={settings.riskProfile} onChange={toggle("riskProfile")} />
          <Text style={styles.chipHint}>Used to rank route suggestions on the map.</Text>
        </View>
      </Section>

      <Section title="Notifications">
        <SettingRow icon={<RowIcon name="alert-circle" color={colors.danger} bg={colors.dangerSoft} />} label="Red zone entry alerts">
          <Switch value={settings.zoneAlerts} onValueChange={toggle("zoneAlerts")} trackColor={switchColors} />
        </SettingRow>
        <SettingRow icon={<RowIcon name="moon" color={colors.warning} bg={colors.warningSoft} />} label="Time-based safety alerts" last>
          <Switch value={settings.timeAlerts} onValueChange={toggle("timeAlerts")} trackColor={switchColors} />
        </SettingRow>
      </Section>

      <Section title="Emergency">
        <SettingRow icon={<RowIcon name="share-social" color={colors.safe} bg={colors.safeSoft} />} label="Share location with emergency contacts">
          <Switch
            value={settings.shareLocationWithContacts}
            onValueChange={toggle("shareLocationWithContacts")}
            trackColor={switchColors}
          />
        </SettingRow>
        <LinkRow
          icon={<RowIcon name="people" color={colors.safe} bg={colors.safeSoft} />}
          label="Manage emergency contacts"
          onPress={() => setSheet("contacts")}
          last
        />
      </Section>

      <Section title="Privacy">
        <LinkRow
          icon={<RowIcon name="lock-closed" />}
          label="How SafeRoute protects your report data"
          onPress={() => setSheet("privacy")}
        />
        <LinkRow icon={<RowIcon name="server" />} label="Data sources and freshness" onPress={() => setSheet("data")} last />
      </Section>

      <MyReportsSheet visible={sheet === "reports"} onClose={closeSheet} />
      <PrivacySheet visible={sheet === "privacy"} onClose={closeSheet} />
      <EmergencyContactsSheet visible={sheet === "contacts"} onClose={closeSheet} />
      <DataStatusSheet visible={sheet === "data"} onClose={closeSheet} />
    </ScrollView>
  );
}

const makeStyles = ({ colors, card, typography }) =>
  StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    content: { padding: spacing.lg, paddingBottom: spacing.xxl },
    section: { ...typography.sectionLabel, marginTop: spacing.lg, marginBottom: spacing.sm, marginLeft: spacing.xs },
    group: { ...card, paddingHorizontal: spacing.lg },
    row: { flexDirection: "row", alignItems: "center", paddingVertical: 13, gap: spacing.md },
    rowDivider: { borderBottomWidth: 1, borderColor: colors.dividerLight },
    rowIcon: { width: 30, height: 30, borderRadius: radius.sm, alignItems: "center", justifyContent: "center" },
    rowLabel: { flex: 1, color: colors.text, fontSize: 15 },
    logout: { color: colors.danger, fontWeight: "700" },
    hint: { flex: 1, color: colors.textMuted, ...typography.caption, lineHeight: 18 },
    chipsWrap: { paddingVertical: spacing.lg },
    chipHint: { color: colors.textSubtle, ...typography.small, marginTop: spacing.sm },
  });
