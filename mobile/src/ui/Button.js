import { ActivityIndicator, StyleSheet, Text, TouchableOpacity } from "react-native";

import { radius, spacing, useTheme, useThemedStyles } from "../theme";

// Full-width call-to-action button. `variant` picks the colour; shows a
// spinner instead of the label while `loading`.
export default function Button({ label, onPress, variant = "primary", loading = false, disabled = false, style }) {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  const background = variant === "danger" ? colors.danger : colors.primary;
  const inactive = disabled || loading;
  return (
    <TouchableOpacity
      style={[styles.button, { backgroundColor: background }, disabled && styles.disabled, style]}
      onPress={onPress}
      disabled={inactive}
    >
      {loading ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={styles.label}>{label}</Text>}
    </TouchableOpacity>
  );
}

// Secondary text-only action (Cancel, "No account? Sign up", ...).
export function TextButton({ label, onPress, muted = false, style }) {
  const styles = useThemedStyles(makeStyles);
  return (
    <TouchableOpacity onPress={onPress}>
      <Text style={[styles.textButton, muted && styles.textButtonMuted, style]}>{label}</Text>
    </TouchableOpacity>
  );
}

const makeStyles = ({ colors }) =>
  StyleSheet.create({
    button: { borderRadius: radius.md, paddingVertical: 14, alignItems: "center", marginBottom: spacing.md },
    disabled: { backgroundColor: colors.primaryDisabled },
    label: { color: colors.onPrimary, fontWeight: "700", fontSize: 15 },
    textButton: { color: colors.primary, fontWeight: "600", textAlign: "center", marginBottom: spacing.sm },
    textButtonMuted: { color: colors.textFaint },
  });
