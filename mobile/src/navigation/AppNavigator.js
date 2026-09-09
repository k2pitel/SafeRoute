import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";

import MapScreen from "../screens/MapScreen";
import NewsScreen from "../screens/NewsScreen";
import CrimeIndexScreen from "../screens/CrimeIndexScreen";
import SettingsScreen from "../screens/SettingsScreen";

const Tab = createBottomTabNavigator();

// Maps each tab to a page from README > Mobile App — Pages. Routing lives
// in a panel on the Map tab itself (see RoutePanel) rather than its own tab.
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
