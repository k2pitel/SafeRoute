import { useState } from "react";
import { ActivityIndicator, Modal, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";

const REPORT_TYPES = [
  { key: "harassment", label: "Harassment" },
  { key: "assault", label: "Assault" },
  { key: "theft", label: "Theft" },
  { key: "suspicious", label: "Suspicious activity" },
  { key: "other", label: "Other" },
];

const TIME_OPTIONS = [
  { label: "Just now", minutesAgo: 0 },
  { label: "15 min ago", minutesAgo: 15 },
  { label: "30 min ago", minutesAgo: 30 },
  { label: "1 hour ago", minutesAgo: 60 },
];

// The "report an incident" form (e.g. harassment in a nightlife area) —
// community reports feed into safety scoring once confirmed by other
// nearby users. Submitting requires login, handled by the caller
// (MapScreen) via AuthPromptModal before this is shown.
export default function ReportModal({ visible, coordinate, onClose, onSubmit }) {
  const [type, setType] = useState(REPORT_TYPES[0].key);
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
      setType(REPORT_TYPES[0].key);
      setDescription("");
      setMinutesAgo(0);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <ScrollView style={styles.card} contentContainerStyle={{ paddingBottom: 12 }}>
          <Text style={styles.title}>Report an incident</Text>
          <Text style={styles.subtitle}>Reported near your current location.</Text>

          <Text style={styles.label}>Type</Text>
          <View style={styles.pillRow}>
            {REPORT_TYPES.map((option) => (
              <TouchableOpacity
                key={option.key}
                style={[styles.pill, type === option.key && styles.pillActive]}
                onPress={() => setType(option.key)}
              >
                <Text style={type === option.key ? styles.pillTextActive : styles.pillText}>{option.label}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>When</Text>
          <View style={styles.pillRow}>
            {TIME_OPTIONS.map((option) => (
              <TouchableOpacity
                key={option.label}
                style={[styles.pill, minutesAgo === option.minutesAgo && styles.pillActive]}
                onPress={() => setMinutesAgo(option.minutesAgo)}
              >
                <Text style={minutesAgo === option.minutesAgo ? styles.pillTextActive : styles.pillText}>
                  {option.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

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

          <TouchableOpacity style={styles.submitButton} onPress={submit} disabled={submitting}>
            {submitting ? <ActivityIndicator color="white" /> : <Text style={styles.submitText}>Submit report</Text>}
          </TouchableOpacity>
          <TouchableOpacity onPress={onClose}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end" },
  card: { backgroundColor: "white", borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: 20, maxHeight: "80%" },
  title: { fontSize: 18, fontWeight: "bold", marginBottom: 4 },
  subtitle: { color: "#666", fontSize: 13, marginBottom: 16 },
  label: { fontSize: 13, color: "#888", textTransform: "uppercase", marginBottom: 8 },
  pillRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 16 },
  pill: { borderWidth: 1, borderColor: "#ccc", borderRadius: 20, paddingVertical: 6, paddingHorizontal: 14 },
  pillActive: { backgroundColor: "#007AFF", borderColor: "#007AFF" },
  pillText: { color: "#333" },
  pillTextActive: { color: "white" },
  textArea: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    textAlignVertical: "top",
  },
  error: { color: "#E5484D", marginBottom: 12 },
  submitButton: { backgroundColor: "#E5484D", borderRadius: 8, paddingVertical: 12, alignItems: "center", marginBottom: 12 },
  submitText: { color: "white", fontWeight: "600" },
  cancelText: { color: "#999", textAlign: "center" },
});
