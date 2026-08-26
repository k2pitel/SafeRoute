import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";

import MapScreen from "../screens/MapScreen";
import RouteScreen from "../screens/RouteScreen";
import NewsScreen from "../screens/NewsScreen";
import CrimeIndexScreen from "../screens/CrimeIndexScreen";
import SettingsScreen from "../screens/SettingsScreen";

const Tab = createBottomTabNavigator();

// Maps each tab to a page from README > Mobile App — Pages.
const ICONS = {
  Map: "map",
  Route: "navigate",
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
      <Tab.Screen name="Map" component={MapScreen} />
      <Tab.Screen name="Route" component={RouteScreen} />
      <Tab.Screen name="News" component={NewsScreen} />
      <Tab.Screen name="Crime Index" component={CrimeIndexScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}
