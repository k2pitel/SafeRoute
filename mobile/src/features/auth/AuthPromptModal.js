import { useState } from "react";
import { StyleSheet, Text, TextInput } from "react-native";

import { colors, inputStyle, spacing } from "../../theme";
import { BottomSheet, Button, TextButton } from "../../ui";
import { useAuth } from "./AuthContext";

// Shown when a signed-out user taps "Report" (UC2 extension 3a) — reporting
// requires an account so reports can't be faked or spammed anonymously.
export default function AuthPromptModal({ visible, onClose, onAuthenticated }) {
  const { login, signup } = useAuth();
  const [mode, setMode] = useState("login"); // 'login' | 'signup'
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const isLogin = mode === "login";

  const submit = async () => {
    setError(null);
    setLoading(true);
    try {
      if (isLogin) await login(email.trim(), password);
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
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={isLogin ? "Log in to report" : "Create an account to report"}
      subtitle="Reporting requires an account so reports can't be faked or spammed."
    >
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

      <Button label={isLogin ? "Log in" : "Sign up"} onPress={submit} loading={loading} />
      <TextButton
        label={isLogin ? "No account? Sign up" : "Already have an account? Log in"}
        onPress={() => setMode(isLogin ? "signup" : "login")}
      />
      <TextButton label="Cancel" onPress={onClose} muted />
    </BottomSheet>
  );
}

const styles = StyleSheet.create({
  input: { ...inputStyle, borderColor: colors.borderLight, padding: spacing.md, marginBottom: spacing.md },
  error: { color: colors.danger, marginBottom: spacing.md },
});
