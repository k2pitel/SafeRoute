import { useState } from "react";
import { ActivityIndicator, Modal, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";

import { useAuth } from "../context/AuthContext";

// Shown when a signed-out user taps "Report" — reporting requires an
// account so reports can't be faked or spammed anonymously.
export default function AuthPromptModal({ visible, onClose, onAuthenticated }) {
  const { login, signup } = useAuth();
  const [mode, setMode] = useState("login"); // 'login' | 'signup'
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setError(null);
    setLoading(true);
    try {
      if (mode === "login") await login(email.trim(), password);
      else await signup(email.trim(), password);
      setEmail("");
      setPassword("");
      onAuthenticated();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <Text style={styles.title}>{mode === "login" ? "Log in to report" : "Create an account to report"}</Text>
          <Text style={styles.subtitle}>Reporting requires an account so reports can't be faked or spammed.</Text>

          <TextInput
            style={styles.input}
            placeholder="Email"
            autoCapitalize="none"
            keyboardType="email-address"
            value={email}
            onChangeText={setEmail}
          />
          <TextInput
            style={styles.input}
            placeholder="Password"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
          />

          {error && <Text style={styles.error}>{error}</Text>}

          <TouchableOpacity style={styles.submitButton} onPress={submit} disabled={loading}>
            {loading ? <ActivityIndicator color="white" /> : (
              <Text style={styles.submitText}>{mode === "login" ? "Log in" : "Sign up"}</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity onPress={() => setMode(mode === "login" ? "signup" : "login")}>
            <Text style={styles.switchText}>
              {mode === "login" ? "No account? Sign up" : "Already have an account? Log in"}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={onClose}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end" },
  card: { backgroundColor: "white", borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: 20 },
  title: { fontSize: 18, fontWeight: "bold", marginBottom: 4 },
  subtitle: { color: "#666", fontSize: 13, marginBottom: 16 },
  input: { borderWidth: 1, borderColor: "#ddd", borderRadius: 8, padding: 12, marginBottom: 12 },
  error: { color: "#E5484D", marginBottom: 12 },
  submitButton: { backgroundColor: "#007AFF", borderRadius: 8, paddingVertical: 12, alignItems: "center", marginBottom: 12 },
  submitText: { color: "white", fontWeight: "600" },
  switchText: { color: "#007AFF", textAlign: "center", marginBottom: 8 },
  cancelText: { color: "#999", textAlign: "center" },
});
