import { useState } from "react";
import { StyleSheet, Text, TextInput } from "react-native";

import { colors, inputStyle, spacing, typography } from "../../theme";
import { BottomSheet, Button, ChipGroup, TextButton } from "../../ui";

// UC2 step 4: incident type + when it happened.
const REPORT_TYPES = [
  { value: "harassment", label: "Harassment" },
  { value: "assault", label: "Assault" },
  { value: "theft", label: "Theft" },
  { value: "suspicious", label: "Suspicious activity" },
  { value: "other", label: "Other" },
];

const TIME_OPTIONS = [
  { value: 0, label: "Just now" },
  { value: 15, label: "15 min ago" },
  { value: 30, label: "30 min ago" },
  { value: 60, label: "1 hour ago" },
];

// The "report an incident" form (UC2, F2) — community reports feed into
// safety scoring once confirmed by other nearby users (F3). Submitting
// requires login, handled by the caller (MapScreen) via AuthPromptModal
// before this is shown.
export default function ReportModal({ visible, coordinate, onClose, onSubmit }) {
  const [type, setType] = useState(REPORT_TYPES[0].value);
  const [description, setDescription] = useState("");
  const [minutesAgo, setMinutesAgo] = useState(0);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit({
        type,
        description: description.trim() || undefined,
        occurred_at: new Date(Date.now() - minutesAgo * 60_000).toISOString(),
        latitude: coordinate.latitude,
        longitude: coordinate.longitude,
      });
      setType(REPORT_TYPES[0].value);
      setDescription("");
      setMinutesAgo(0);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title="Report an incident"
      subtitle="Reported near your current location."
    >
      <Text style={styles.label}>Type</Text>
      <ChipGroup options={REPORT_TYPES} value={type} onChange={setType} style={styles.group} />

      <Text style={styles.label}>When</Text>
      <ChipGroup options={TIME_OPTIONS} value={minutesAgo} onChange={setMinutesAgo} style={styles.group} />

      <Text style={styles.label}>Details (optional)</Text>
      <TextInput
        style={styles.textArea}
        placeholder="What happened?"
        multiline
        numberOfLines={4}
        value={description}
        onChangeText={setDescription}
      />

      {error && <Text style={styles.error}>{error}</Text>}

      <Button label="Submit report" variant="danger" onPress={submit} loading={submitting} />
      <TextButton label="Cancel" onPress={onClose} muted />
    </BottomSheet>
  );
}

const styles = StyleSheet.create({
  label: { ...typography.sectionLabel, marginBottom: spacing.sm },
  group: { marginBottom: spacing.lg },
  textArea: {
    ...inputStyle,
    borderColor: colors.borderLight,
    padding: spacing.md,
    marginBottom: spacing.lg,
    textAlignVertical: "top",
  },
  error: { color: colors.danger, marginBottom: spacing.md },
});
