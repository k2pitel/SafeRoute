import { useEffect, useRef, useState } from "react";
import { View, TextInput, FlatList, TouchableOpacity, Text, StyleSheet, ActivityIndicator } from "react-native";

import { searchPlaces } from "../services/geocoding";

// Type-ahead place search, e.g. type "aarhus" and pick from the matching
// places (like a train-app station picker) instead of typing raw lat/lon.
export default function PlaceSearchInput({ placeholder, value, onSelect, rightAccessory, near }) {
  const [query, setQuery] = useState(value || "");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [focused, setFocused] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => setQuery(value || ""), [value]);

  const handleChange = (text) => {
    setQuery(text);
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (text.trim().length < 2) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      const places = await searchPlaces(text, { near });
      setResults(places);
      setLoading(false);
    }, 400);
  };

  const handleSelect = (place) => {
    setQuery(place.primary);
    setResults([]);
    setFocused(false);
    onSelect(place);
  };

  const showDropdown = focused && (results.length > 0 || loading);

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
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    padding: 10,
  },
  dropdown: {
    position: "absolute",
    top: "100%",
    left: 0,
    right: 0,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    marginTop: 4,
    maxHeight: 220,
    elevation: 6,
    shadowColor: "#000",
    shadowOpacity: 0.15,
    shadowRadius: 6,
    zIndex: 20,
  },
  loading: { padding: 10 },
  resultRow: { paddingVertical: 10, paddingHorizontal: 12, borderBottomWidth: 1, borderBottomColor: "#f0f0f0" },
  resultPrimary: { color: "#222", fontWeight: "600" },
  resultSecondary: { color: "#888", fontSize: 12, marginTop: 2 },
});
