import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";

import MapScreen from "../features/map/MapScreen";
import NewsScreen from "../features/news/NewsScreen";
import CrimeIndexScreen from "../features/crimeIndex/CrimeIndexScreen";
import SettingsScreen from "../features/settings/SettingsScreen";
import { useTheme } from "../theme";

const Tab = createBottomTabNavigator();

// The screens from the product vision (afsnit 3.2.1): Kort, Nyheder,
// Bytryghedsoversigt, Indstillinger. Rute lives as a panel on the Map tab
// (features/routes/RoutePanel) rather than its own tab.
const ICONS = {
  Map: ["map", "map-outline"],
  News: ["newspaper", "newspaper-outline"],
  "Crime Index": ["stats-chart", "stats-chart-outline"],
  Settings: ["settings", "settings-outline"],
};

export default function AppNavigator() {
  const { colors } = useTheme();
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ color, size, focused }) => {
          const [active, inactive] = ICONS[route.name] || ["ellipse", "ellipse-outline"];
          return <Ionicons name={focused ? active : inactive} size={size} color={color} />;
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textFaint,
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
        tabBarStyle: { backgroundColor: colors.surface, borderTopColor: colors.divider },
        headerStyle: { backgroundColor: colors.surface, elevation: 0, shadowOpacity: 0, borderBottomWidth: 1, borderBottomColor: colors.divider },
        headerTitleStyle: { fontWeight: "700", color: colors.text },
        headerTintColor: colors.primary,
      })}
      sceneContainerStyle={{ backgroundColor: colors.background }}
    >
      <Tab.Screen name="Map" component={MapScreen} options={{ title: "Plan a route", tabBarLabel: "Map" }} />
      <Tab.Screen name="News" component={NewsScreen} options={{ title: "SafeRoute" }} />
      <Tab.Screen name="Crime Index" component={CrimeIndexScreen} options={{ title: "SafeRoute" }} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}
