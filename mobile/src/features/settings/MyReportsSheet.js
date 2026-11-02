import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { api } from "../../services/api";
import { radius, spacing, useTheme, useThemedStyles } from "../../theme";
import { BottomSheet, StateView, TextButton } from "../../ui";

// US-38: the signed-in user's own reports, with verification status (F3).
export default function MyReportsSheet({ visible, onClose }) {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  const [reports, setReports] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!visible) return;
    setReports(null);
    setError(null);
    api.getMyReports().then(setReports).catch(setError);
  }, [visible]);

  let body;
  if (error) {
    body = <StateView tone="error" icon="alert-circle-outline" title="Couldn't load your reports" message={error.message} />;
  } else if (!reports) {
    body = <ActivityIndicator color={colors.primary} style={styles.spinner} />;
  } else if (reports.length === 0) {
    body = <StateView icon="document-text-outline" title="No reports yet" message="Reports you submit from the map show up here." />;
  } else {
    body = reports.map((r) => {
      const status = r.verified ? "Verified" : r.confirmations > 0 ? `${r.confirmations} confirmed` : "Unconfirmed";
      const tint = r.verified ? colors.safe : r.confirmations > 0 ? colors.warning : colors.textSubtle;
      const soft = r.verified ? colors.safeSoft : r.confirmations > 0 ? colors.warningSoft : colors.surfaceMuted;
      return (
        <View key={r.id} style={styles.row}>
          <View style={styles.rowTop}>
            <Text style={styles.type}>{r.type}</Text>
            <View style={[styles.chip, { backgroundColor: soft }]}>
              <Text style={[styles.chipText, { color: tint }]}>{status}</Text>
            </View>
          </View>
          <Text style={styles.meta}>{new Date(r.occurred_at).toLocaleString()}</Text>
          {r.description ? <Text style={styles.description}>{r.description}</Text> : null}
        </View>
      );
    });
  }

  return (
    <BottomSheet visible={visible} onClose={onClose} title="My reports" subtitle="Only you can see this list. Others never see who reported.">
      {body}
      <TextButton label="Close" onPress={onClose} muted style={styles.close} />
    </BottomSheet>
  );
}

const makeStyles = ({ colors }) =>
  StyleSheet.create({
    spinner: { marginVertical: spacing.xl },
    row: { paddingVertical: spacing.md, borderBottomWidth: 1, borderColor: colors.dividerLight },
    rowTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
    type: { color: colors.text, fontWeight: "700", fontSize: 15, textTransform: "capitalize" },
    chip: { borderRadius: radius.pill, paddingVertical: 2, paddingHorizontal: 10 },
    chipText: { fontSize: 12, fontWeight: "700" },
    meta: { color: colors.textSubtle, fontSize: 12, marginTop: 2 },
    description: { color: colors.textBody, marginTop: 4 },
    close: { marginTop: spacing.lg },
  });
