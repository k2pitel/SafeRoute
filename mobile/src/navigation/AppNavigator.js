import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";

import MapScreen from "../features/map/MapScreen";
import NewsScreen from "../features/news/NewsScreen";
import CrimeIndexScreen from "../features/crimeIndex/CrimeIndexScreen";
import SettingsScreen from "../features/settings/SettingsScreen";

const Tab = createBottomTabNavigator();

// The screens from the product vision (afsnit 3.2.1): Kort, Nyheder,
// Bytryghedsoversigt, Indstillinger. Rute lives as a panel on the Map tab
// (features/routes/RoutePanel) rather than its own tab.
const ICONS = {
  Map: "map",
  News: "newspaper",
  "Crime Index": "stats-chart",
  Settings: "settings",
};

export default function AppNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ color, size }) => (
          <Ionicons name={ICONS[route.name] || "ellipse"} size={size} color={color} />
        ),
      })}
    >
      <Tab.Screen name="Map" component={MapScreen} options={{ title: "Plan a route", tabBarLabel: "Map" }} />
      <Tab.Screen name="News" component={NewsScreen} />
      <Tab.Screen name="Crime Index" component={CrimeIndexScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}
