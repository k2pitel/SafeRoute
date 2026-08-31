import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import AppNavigator from "./src/navigation/AppNavigator";
import { ActiveRouteProvider } from "./src/context/ActiveRouteContext";

export default function App() {
  return (
    <ActiveRouteProvider>
      <NavigationContainer>
        <StatusBar style="auto" />
        <AppNavigator />
      </NavigationContainer>
    </ActiveRouteProvider>
  );
}
