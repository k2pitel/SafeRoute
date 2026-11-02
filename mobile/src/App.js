import { StatusBar } from "expo-status-bar";
import { DarkTheme, DefaultTheme, NavigationContainer } from "@react-navigation/native";

import AppNavigator from "./navigation/AppNavigator";
import { AuthProvider } from "./features/auth/AuthContext";
import { ActiveRouteProvider } from "./features/routes/ActiveRouteContext";
import { SettingsProvider, useSettings } from "./features/settings/SettingsContext";
import { ThemeProvider, useTheme } from "./theme";

// Navigation chrome (tab bar, header, scene background) in the active palette.
function ThemedNavigation() {
  const { dark, colors } = useTheme();
  const base = dark ? DarkTheme : DefaultTheme;
  const navTheme = {
    ...base,
    dark,
    colors: {
      ...base.colors,
      primary: colors.primary,
      background: colors.background,
      card: colors.surface,
      text: colors.text,
      border: colors.divider,
      notification: colors.danger,
    },
  };
  return (
    <NavigationContainer theme={navTheme}>
      <StatusBar style={dark ? "light" : "dark"} />
      <AppNavigator />
    </NavigationContainer>
  );
}

// Settings → Appearance decides light/dark; "system" follows the phone.
function ThemedApp() {
  const { settings } = useSettings();
  return (
    <ThemeProvider preference={settings.appearance}>
      <ThemedNavigation />
    </ThemeProvider>
  );
}

// Root: app-wide state (contexts) around the tab navigator.
export default function App() {
  return (
    <AuthProvider>
      <SettingsProvider>
        <ActiveRouteProvider>
          <ThemedApp />
        </ActiveRouteProvider>
      </SettingsProvider>
    </AuthProvider>
  );
}
