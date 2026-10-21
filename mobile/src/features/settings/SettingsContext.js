import { createContext, useContext, useEffect, useState } from "react";
import * as SecureStore from "expo-secure-store";

const SETTINGS_KEY = "saferoute_settings";

// F6: the user's risk profile and notification preferences. Read by the
// route ranking (features/routes/rankRoutes) and the walk monitor's
// geofence (features/walk/useWalkMonitor); persisted so they survive a
// restart.
export const DEFAULT_SETTINGS = {
  riskProfile: "balanced", // 'fast' | 'balanced' | 'safest'
  zoneAlerts: true, // F5: alert on entering an unsafe zone
  timeAlerts: true, // F5: alert at hours when unsafety historically rises
  shareLocationWithContacts: false,
};

const SettingsContext = createContext(null);

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);

  useEffect(() => {
    SecureStore.getItemAsync(SETTINGS_KEY)
      .then((json) => json && setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(json) }))
      .catch(() => {}); // unreadable/absent storage: keep defaults
  }, []);

  const updateSetting = (key, value) => {
    setSettings((prev) => {
      const next = { ...prev, [key]: value };
      SecureStore.setItemAsync(SETTINGS_KEY, JSON.stringify(next)).catch(() => {});
      return next;
    });
  };

  return <SettingsContext.Provider value={{ settings, updateSetting }}>{children}</SettingsContext.Provider>;
}

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within SettingsProvider");
  return ctx;
}
