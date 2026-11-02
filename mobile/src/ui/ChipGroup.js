import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

import { radius, spacing, useThemedStyles } from "../theme";

// Single-choice selector rendered as a row of pills (report type, time,
// risk profile, ...). options: [{ value, label }].
export default function ChipGroup({ options, value, onChange, style }) {
  const styles = useThemedStyles(makeStyles);
  return (
    <View style={[styles.row, style]}>
      {options.map((option) => {
        const active = option.value === value;
        return (
          <TouchableOpacity
            key={String(option.value)}
            style={[styles.chip, active && styles.chipActive]}
            onPress={() => onChange(option.value)}
          >
            <Text style={active ? styles.textActive : styles.text}>{option.label}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const makeStyles = ({ colors }) =>
  StyleSheet.create({
    row: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
    chip: {
      borderWidth: 1,
      borderColor: colors.border,
      backgroundColor: colors.surface,
      borderRadius: radius.pill,
      paddingVertical: 6,
      paddingHorizontal: 14,
    },
    chipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
    text: { color: colors.textStrong, fontWeight: "500" },
    textActive: { color: colors.onPrimary, fontWeight: "600" },
  });
