import { StyleSheet, Text, View } from "react-native";

import { colors, elevation, radius, spacing, typography } from "../theme";
import { TextButton } from "./Button";

// Card floating at the bottom of the map with details about one tapped
// marker (F8). `actions`: [{ label, onPress }] shown as a row of links.
export default function InfoCard({ title, children, actions = [] }) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      {children}
      <View style={styles.actions}>
        {actions.map((action) => (
          <TextButton key={action.label} label={action.label} onPress={action.onPress} style={styles.action} />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    position: "absolute",
    bottom: spacing.xl,
    left: spacing.xl,
    right: spacing.xl,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    ...elevation,
  },
  title: { ...typography.heading, marginBottom: spacing.xs, textTransform: "capitalize" },
  actions: { flexDirection: "row", justifyContent: "space-between" },
  action: { marginTop: spacing.sm, marginBottom: 0 },
});
