import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";

import AppNavigator from "./navigation/AppNavigator";
import { AuthProvider } from "./features/auth/AuthContext";
import { ActiveRouteProvider } from "./features/routes/ActiveRouteContext";
import { SettingsProvider } from "./features/settings/SettingsContext";

// Root: app-wide state (contexts) around the tab navigator.
export default function App() {
  return (
    <AuthProvider>
      <SettingsProvider>
        <ActiveRouteProvider>
          <NavigationContainer>
            <StatusBar style="auto" />
            <AppNavigator />
          </NavigationContainer>
        </ActiveRouteProvider>
      </SettingsProvider>
    </AuthProvider>
  );
}
