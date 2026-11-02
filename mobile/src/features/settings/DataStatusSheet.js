import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { api } from "../../services/api";
import { radius, spacing, useTheme, useThemedStyles } from "../../theme";
import { BottomSheet, StateView, TextButton } from "../../ui";

// DP-07: which data the app is using and whether the background jobs are healthy.
const JOB_NAMES = {
  poll_news: "News feeds",
  refresh_crime_stats: "Crime statistics",
  recalculate_segment_scores: "Safety scores",
  purge_expired_reports: "Old report clean-up",
  relocate_news: "News placement",
};

function ago(iso) {
  if (!iso) return "never";
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  return hours < 48 ? `${hours} h ago` : new Date(iso).toLocaleDateString();
}

export default function DataStatusSheet({ visible, onClose }) {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!visible) return;
    setStatus(null);
    setError(null);
    api.getPipelineStatus().then(setStatus).catch(setError);
  }, [visible]);

  let body;
  if (error) {
    body = <StateView tone="error" icon="cloud-offline-outline" title="Can't reach the server" message={error.message} />;
  } else if (!status) {
    body = <ActivityIndicator color={colors.primary} style={styles.spinner} />;
  } else {
    const crime = status.datasets.crime_statistics;
    const news = status.datasets.news;
    body = (
      <>
        <Text style={styles.section}>Data</Text>
        <View style={styles.card}>
          <Text style={styles.name}>Crime statistics</Text>
          <Text style={styles.meta}>
            {crime.source} · {crime.period ? `period ${crime.period}` : "not loaded yet"}
          </Text>
          <Text style={styles.meta}>Fetched {ago(crime.fetched_at)}</Text>
        </View>
        <View style={styles.card}>
          <Text style={styles.name}>Crime news</Text>
          <Text style={styles.meta}>{news.source}</Text>
          <Text style={styles.meta}>
            {news.archived} articles · newest {ago(news.newest_published_at)}
          </Text>
        </View>

        <Text style={styles.section}>Background jobs</Text>
        {status.jobs.map((job) => {
          const ok = !job.stale && !(job.last_error_at && (!job.last_success || job.last_error_at > job.last_success));
          return (
            <View key={job.job} style={styles.jobRow}>
              <View style={[styles.dot, { backgroundColor: ok ? colors.safe : colors.warning }]} />
              <Text style={styles.jobName}>{JOB_NAMES[job.job] || job.job}</Text>
              <Text style={styles.jobMeta}>{job.runs ? `OK ${ago(job.last_success)}` : "waiting"}</Text>
            </View>
          );
        })}
      </>
    );
  }

  return (
    <BottomSheet visible={visible} onClose={onClose} title="Data sources" subtitle="Where the map's numbers come from and how fresh they are.">
      {body}
      <TextButton label="Close" onPress={onClose} muted style={styles.close} />
    </BottomSheet>
  );
}

const makeStyles = ({ colors, typography }) =>
  StyleSheet.create({
    spinner: { marginVertical: spacing.xl },
    section: { ...typography.sectionLabel, marginTop: spacing.md, marginBottom: spacing.sm },
    card: { backgroundColor: colors.surfaceMuted, borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.sm },
    name: { color: colors.text, fontWeight: "700" },
    meta: { color: colors.textMuted, fontSize: 12, marginTop: 2 },
    jobRow: { flexDirection: "row", alignItems: "center", paddingVertical: 6, gap: spacing.sm },
    dot: { width: 8, height: 8, borderRadius: 4 },
    jobName: { flex: 1, color: colors.textBody },
    jobMeta: { color: colors.textSubtle, fontSize: 12 },
    close: { marginTop: spacing.lg },
  });
