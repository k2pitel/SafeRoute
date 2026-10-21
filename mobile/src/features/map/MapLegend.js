import { StyleSheet, Text, View } from "react-native";

import { colors, elevation, radius, spacing, typography } from "../../theme";

// Explains the marker colours. entries: [{ color, label }]; hidden when empty.
export default function MapLegend({ entries }) {
  if (entries.length === 0) return null;
  return (
    <View style={styles.legend}>
      {entries.map((entry) => (
        <View key={entry.label} style={styles.row}>
          <View style={[styles.dot, { backgroundColor: entry.color }]} />
          <Text style={styles.text}>{entry.label}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  legend: {
    position: "absolute",
    left: spacing.lg,
    bottom: 100,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: 10,
    ...elevation,
  },
  row: { flexDirection: "row", alignItems: "center", marginVertical: 2 },
  dot: { width: 10, height: 10, borderRadius: 5, marginRight: spacing.sm },
  text: { ...typography.small, color: colors.textStrong },
});
