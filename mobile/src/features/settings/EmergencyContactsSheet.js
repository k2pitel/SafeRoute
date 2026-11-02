import { useEffect, useState } from "react";
import { StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { spacing, useTheme, useThemedStyles } from "../../theme";
import { BottomSheet, Button, TextButton } from "../../ui";
import { loadContacts, saveContacts } from "./emergencyContacts";

const MAX_CONTACTS = 5;

// US-26: add and remove emergency contacts (stored on this phone only).
export default function EmergencyContactsSheet({ visible, onClose }) {
  const { colors } = useTheme();
  const styles = useThemedStyles(makeStyles);
  const [contacts, setContacts] = useState([]);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    if (visible) loadContacts().then(setContacts);
  }, [visible]);

  const update = async (next) => {
    setContacts(next);
    await saveContacts(next);
  };

  const add = async () => {
    const cleaned = phone.replace(/[^\d+]/g, "");
    if (!name.trim() || cleaned.length < 8) {
      setError("Enter a name and a phone number (at least 8 digits).");
      return;
    }
    setError(null);
    await update([...contacts, { id: String(Date.now()), name: name.trim(), phone: cleaned }]);
    setName("");
    setPhone("");
  };

  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title="Emergency contacts"
      subtitle="Stored only on this phone. During a walk you can text them your location in one tap."
    >
      {contacts.map((c) => (
        <View key={c.id} style={styles.row}>
          <Ionicons name="person-circle-outline" size={26} color={colors.primary} />
          <View style={styles.rowText}>
            <Text style={styles.name}>{c.name}</Text>
            <Text style={styles.phone}>{c.phone}</Text>
          </View>
          <TouchableOpacity onPress={() => update(contacts.filter((x) => x.id !== c.id))} hitSlop={10}>
            <Ionicons name="trash-outline" size={20} color={colors.danger} />
          </TouchableOpacity>
        </View>
      ))}

      {contacts.length < MAX_CONTACTS && (
        <>
          <TextInput
            style={styles.input}
            placeholder="Name"
            placeholderTextColor={colors.textFaint}
            value={name}
            onChangeText={setName}
          />
          <TextInput
            style={styles.input}
            placeholder="Phone, e.g. +45 12 34 56 78"
            placeholderTextColor={colors.textFaint}
            keyboardType="phone-pad"
            value={phone}
            onChangeText={setPhone}
          />
          {error && <Text style={styles.error}>{error}</Text>}
          <Button label="Add contact" onPress={add} />
        </>
      )}
      <TextButton label="Done" onPress={onClose} muted />
    </BottomSheet>
  );
}

const makeStyles = ({ colors, inputStyle }) =>
  StyleSheet.create({
    row: {
      flexDirection: "row",
      alignItems: "center",
      gap: spacing.md,
      paddingVertical: spacing.sm,
      borderBottomWidth: 1,
      borderColor: colors.dividerLight,
    },
    rowText: { flex: 1 },
    name: { color: colors.text, fontWeight: "600" },
    phone: { color: colors.textSubtle, fontSize: 12 },
    input: { ...inputStyle, marginTop: spacing.md },
    error: { color: colors.danger, marginTop: spacing.sm },
  });
