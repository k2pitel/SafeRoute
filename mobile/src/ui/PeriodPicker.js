import { useState } from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { radius, spacing, useTheme, useThemedStyles } from "../theme";

// Year-range filter (map news pins, News tab). `value` is null (the
// default view, labelled by `defaultLabel`) or { from, to } in whole
// years; `range` is { min_year, max_year } for the data being filtered.
function presetsFor(max, defaultLabel) {
  return [
    { key: "default", label: defaultLabel, value: null },
    { key: "1", label: String(max), value: { from: max, to: max } },
    { key: "2", label: `${max - 1}–${max}`, value: { from: max - 1, to: max } },
    { key: "5", label: `${max - 4}–${max}`, value: { from: max - 4, to: max } },
  ];
}

const same = (a, b) => (a === null && b === null) || (a && b && a.from === b.from && a.to === b.to);

function Stepper({ value, min, max, onChange }) {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  return (
    <View style={styles.stepper}>
      <TouchableOpacity onPress={() => onChange(value - 1)} disabled={value <= min} hitSlop={8}>
        <Ionicons name="chevron-back" size={20} color={value <= min ? colors.border : colors.primary} />
      </TouchableOpacity>
      <Text style={styles.stepperValue}>{value}</Text>
      <TouchableOpacity onPress={() => onChange(value + 1)} disabled={value >= max} hitSlop={8}>
        <Ionicons name="chevron-forward" size={20} color={value >= max ? colors.border : colors.primary} />
      </TouchableOpacity>
    </View>
  );
}

export default function PeriodPicker({ value, range, onChange, note, defaultLabel = "Latest" }) {
  const styles = useThemedStyles(makeStyles);
  const [custom, setCustom] = useState(false);
  if (!range) return null;
  const { min_year: min, max_year: max } = range;
  const presets = presetsFor(max, defaultLabel);
  const isPreset = presets.some((p) => same(p.value, value));
  const showCustom = custom || !isPreset;
  const current = value || { from: max - 1, to: max };

  return (
    <View style={styles.wrap}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
        <Ionicons name="calendar-outline" size={16} color={styles.label.color} style={styles.icon} />
        {presets.map((p) => {
          const active = !showCustom && same(p.value, value);
          return (
            <TouchableOpacity
              key={p.key}
              style={[styles.chip, active && styles.chipActive]}
              onPress={() => {
                setCustom(false);
                onChange(p.value);
              }}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>{p.label}</Text>
            </TouchableOpacity>
          );
        })}
        <TouchableOpacity
          style={[styles.chip, showCustom && styles.chipActive]}
          onPress={() => {
            setCustom(true);
            if (!value) onChange(current);
          }}
        >
          <Text style={[styles.chipText, showCustom && styles.chipTextActive]}>Custom</Text>
        </TouchableOpacity>
      </ScrollView>

      {showCustom && (
        <View style={styles.customRow}>
          <Text style={styles.label}>From</Text>
          <Stepper
            value={current.from}
            min={min}
            max={current.to}
            onChange={(from) => onChange({ from, to: current.to })}
          />
          <Text style={styles.label}>to</Text>
          <Stepper
            value={current.to}
            min={current.from}
            max={max}
            onChange={(to) => onChange({ from: current.from, to })}
          />
        </View>
      )}
      {note ? <Text style={styles.note}>{note}</Text> : null}
    </View>
  );
}

const makeStyles = ({ colors }) =>
  StyleSheet.create({
    wrap: { marginTop: spacing.sm, marginBottom: spacing.xs },
    row: { alignItems: "center", gap: spacing.sm, paddingVertical: 2 },
    icon: { marginRight: 2 },
    chip: {
      paddingVertical: 5,
      paddingHorizontal: 12,
      borderRadius: radius.pill,
      backgroundColor: colors.surface,
      borderWidth: 1,
      borderColor: colors.borderLight,
    },
    chipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
    chipText: { color: colors.textBody, fontWeight: "600", fontSize: 13 },
    chipTextActive: { color: colors.onPrimary },
    customRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, marginTop: spacing.sm },
    label: { color: colors.textSubtle, fontSize: 13 },
    stepper: {
      flexDirection: "row",
      alignItems: "center",
      gap: 6,
      backgroundColor: colors.surface,
      borderWidth: 1,
      borderColor: colors.borderLight,
      borderRadius: radius.md,
      paddingHorizontal: 8,
      paddingVertical: 4,
    },
    stepperValue: { color: colors.text, fontWeight: "700", fontVariant: ["tabular-nums"], minWidth: 40, textAlign: "center" },
    note: { color: colors.textSubtle, fontSize: 11, marginTop: 6 },
  });
