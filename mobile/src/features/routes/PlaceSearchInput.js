import { useEffect, useRef, useState } from "react";
import { View, TextInput, TouchableOpacity, Text, StyleSheet, ActivityIndicator } from "react-native";

import { searchPlaces } from "../../services/geocoding";
import { colors, inputStyle, radius } from "../../theme";

// Type-ahead place search, e.g. type "aarhus" and pick from the matching
// places (like a train-app station picker) instead of typing raw lat/lon.
export default function PlaceSearchInput({ placeholder, value, onSelect, rightAccessory, near }) {
  const [query, setQuery] = useState(value || "");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [focused, setFocused] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => setQuery(value || ""), [value]);

  const handleChange = (text) => {
    setQuery(text);
    if (debounceRef.current) clearTimeout(debounceRef.current);

    setError(null);
    if (text.trim().length < 2) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      try {
        setResults(await searchPlaces(text, { near }));
      } catch (e) {
        setResults([]);
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }, 400);
  };

  const handleSelect = (place) => {
    setQuery(place.primary);
    setResults([]);
    setFocused(false);
    onSelect(place);
  };

  const showDropdown = focused && (results.length > 0 || loading || error);

  return (
    <View style={styles.wrapper}>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={query}
          onChangeText={handleChange}
          placeholder={placeholder}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 150)}
        />
        {rightAccessory}
      </View>

      {showDropdown && (
        <View style={styles.dropdown}>
          {loading && <ActivityIndicator style={styles.loading} size="small" />}
          {error && <Text style={styles.error}>{error}</Text>}
          {results.map((item) => (
            <TouchableOpacity key={item.id} style={styles.resultRow} onPress={() => handleSelect(item)}>
              <Text numberOfLines={1} style={styles.resultPrimary}>
                {item.primary}
              </Text>
              <Text numberOfLines={1} style={styles.resultSecondary}>
                {item.secondary}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { position: "relative", zIndex: 10 },
  inputRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  input: { ...inputStyle, flex: 1 },
  dropdown: {
    position: "absolute",
    top: "100%",
    left: 0,
    right: 0,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.borderLight,
    borderRadius: radius.sm,
    marginTop: 4,
    maxHeight: 220,
    elevation: 6,
    shadowColor: "#000",
    shadowOpacity: 0.15,
    shadowRadius: 6,
    zIndex: 20,
  },
  loading: { padding: 10 },
  error: { padding: 10, color: colors.danger },
  resultRow: { paddingVertical: 10, paddingHorizontal: 12, borderBottomWidth: 1, borderBottomColor: colors.dividerLight },
  resultPrimary: { color: colors.text, fontWeight: "600" },
  resultSecondary: { color: colors.textSubtle, fontSize: 12, marginTop: 2 },
});
