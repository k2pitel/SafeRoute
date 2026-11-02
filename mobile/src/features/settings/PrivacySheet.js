import { StyleSheet, Text } from "react-native";

import { spacing, useThemedStyles } from "../../theme";
import { BottomSheet, TextButton } from "../../ui";

// US-18 / US-59: "How SafeRoute protects your report data" — what is
// stored, what others can see, and the user's rights. Keep in sync with
// the backend (config.py retention, ReportOut, worker/scoring/baseline.py).
const SECTIONS = [
  {
    title: "What we store",
    body:
      "Your email and a salted password hash (never the password itself). For each report: type, " +
      "time, position, optional description and how many others confirmed it.",
  },
  {
    title: "What others see",
    body:
      "Reports are shown without any link to you. Pins are drawn 30–80 m from where you reported, so " +
      "they never point at a doorstep. Old reports disappear from the map after 24 hours.",
  },
  {
    title: "Safety scores",
    body:
      "Report counts feed into route safety scores with random noise added (differential privacy, " +
      "ε = 1), so no score reveals whether one particular report exists.",
  },
  {
    title: "Your location",
    body:
      "Your position is used on the phone to show the map and to warn you during a walk. It is only " +
      "sent to the server as the start of a route search or the place of a report you submit.",
  },
  {
    title: "How long we keep it",
    body: "Reports and their confirmations are deleted automatically after 12 months.",
  },
  {
    title: "Your rights (GDPR)",
    body:
      "Under Settings → Account you can export everything stored about you as a file, or delete your " +
      "account. Deleting removes your account, your reports and your confirmations straight away.",
  },
];

export default function PrivacySheet({ visible, onClose }) {
  const styles = useThemedStyles(makeStyles);
  return (
    <BottomSheet visible={visible} onClose={onClose} title="Your data and privacy">
      {SECTIONS.map((s) => (
        <Text key={s.title} style={styles.para}>
          <Text style={styles.heading}>{s.title}. </Text>
          {s.body}
        </Text>
      ))}
      <TextButton label="Close" onPress={onClose} muted style={styles.close} />
    </BottomSheet>
  );
}

const makeStyles = ({ colors }) =>
  StyleSheet.create({
    para: { color: colors.textBody, lineHeight: 21, marginBottom: spacing.md },
    heading: { color: colors.text, fontWeight: "700" },
    close: { marginTop: spacing.sm },
  });
