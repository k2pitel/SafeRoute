import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { radius, spacing, useTheme, useThemedStyles } from "../theme";

// Centered icon + message for empty and error states, with an optional
// retry action. Screens use it instead of silently showing an empty list.
export default function StateView({ icon = "information-circle-outline", tone = "neutral", title, message, actionLabel, onAction }) {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  const tint = tone === "error" ? colors.danger : colors.primary;
  const soft = tone === "error" ? colors.dangerSoft : colors.primarySoft;
  return (
    <View style={styles.container}>
      <View style={[styles.iconCircle, { backgroundColor: soft }]}>
        <Ionicons name={icon} size={28} color={tint} />
      </View>
      {title ? <Text style={styles.title}>{title}</Text> : null}
      {message ? <Text style={styles.message}>{message}</Text> : null}
      {actionLabel ? (
        <TouchableOpacity style={[styles.action, { backgroundColor: tint }]} onPress={onAction}>
          <Text style={styles.actionText}>{actionLabel}</Text>
        </TouchableOpacity>
      ) : null}
    </View>
  );
}

const makeStyles = ({ colors, typography }) =>
  StyleSheet.create({
    container: { alignItems: "center", paddingVertical: spacing.xxl * 1.5, paddingHorizontal: spacing.xl },
    iconCircle: { width: 60, height: 60, borderRadius: 30, alignItems: "center", justifyContent: "center", marginBottom: spacing.md },
    title: { ...typography.heading, textAlign: "center", marginBottom: spacing.xs },
    message: { color: colors.textMuted, textAlign: "center", lineHeight: 20 },
    action: { marginTop: spacing.lg, borderRadius: radius.pill, paddingVertical: 10, paddingHorizontal: 22 },
    actionText: { color: colors.onPrimary, fontWeight: "700" },
  });
