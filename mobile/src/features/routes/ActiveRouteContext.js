import { createContext, useContext, useState } from "react";

// Shared between RoutePanel (where a route is picked) and MapScreen (where
// it gets drawn) — kept as context rather than local state since MapScreen
// and MapScreen.web both need to read it, and only one of the two mounts.
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
