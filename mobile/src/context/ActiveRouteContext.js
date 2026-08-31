import { createContext, useContext, useState } from "react";

// Shared between RouteScreen (where a route is picked) and MapScreen
// (where it gets drawn) — the two live on separate tabs, so a plain
// TextInput-lifted-state approach doesn't reach across them.
const ActiveRouteContext = createContext(null);

export function ActiveRouteProvider({ children }) {
  const [activeRoute, setActiveRoute] = useState(null);
  // activeRoute shape: { origin: {latitude, longitude, label}, destination: {...}, option: RouteOption }
  return (
    <ActiveRouteContext.Provider value={{ activeRoute, setActiveRoute }}>
      {children}
    </ActiveRouteContext.Provider>
  );
}

export function useActiveRoute() {
  const ctx = useContext(ActiveRouteContext);
  if (!ctx) throw new Error("useActiveRoute must be used within ActiveRouteProvider");
  return ctx;
}
