import { ActivityIndicator, StyleSheet, Text, TouchableOpacity } from "react-native";

import { colors, radius, spacing } from "../theme";

const VARIANT_BACKGROUND = { primary: colors.primary, danger: colors.danger };

// Full-width call-to-action button. `variant` picks the colour; shows a
// spinner instead of the label while `loading`.
export default function Button({ label, onPress, variant = "primary", loading = false, disabled = false, style }) {
  const inactive = disabled || loading;
  return (
    <TouchableOpacity
      style={[
        styles.button,
        { backgroundColor: VARIANT_BACKGROUND[variant] },
        disabled && styles.disabled,
        style,
      ]}
      onPress={onPress}
      disabled={inactive}
    >
      {loading ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={styles.label}>{label}</Text>}
    </TouchableOpacity>
  );
}

// Secondary text-only action (Cancel, "No account? Sign up", ...).
export function TextButton({ label, onPress, muted = false, style }) {
  return (
    <TouchableOpacity onPress={onPress}>
      <Text style={[styles.textButton, muted && styles.textButtonMuted, style]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: { borderRadius: radius.sm, paddingVertical: spacing.md, alignItems: "center", marginBottom: spacing.md },
  disabled: { backgroundColor: colors.primaryDisabled },
  label: { color: colors.onPrimary, fontWeight: "600" },
  textButton: { color: colors.primary, textAlign: "center", marginBottom: spacing.sm },
  textButtonMuted: { color: colors.textFaint },
});
