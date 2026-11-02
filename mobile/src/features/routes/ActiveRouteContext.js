import { createContext, useContext, useState } from "react";

// Shared between RoutePanel (where a route is picked) and MapScreen (where
// it gets drawn) — kept as context rather than local state since MapScreen
// and MapScreen.web both need to read it, and only one of the two mounts.
//
// US-24: picking a route only draws it. Monitoring (F5) starts when the
// user taps "Start walk", as in figur 4.5 ("trykker start gåtur").
const ActiveRouteContext = createContext(null);

export function ActiveRouteProvider({ children }) {
  // activeRoute shape: { origin: {latitude, longitude, label}, destination: {...}, option: RouteOption, mode }
  const [activeRoute, setRoute] = useState(null);
  const [walking, setWalking] = useState(false);

  // A new (or cleared) route always stops an ongoing walk.
  const setActiveRoute = (route) => {
    setWalking(false);
    setRoute(route);
  };

  return (
    <ActiveRouteContext.Provider value={{ activeRoute, setActiveRoute, walking, setWalking }}>
      {children}
    </ActiveRouteContext.Provider>
  );
}

export function useActiveRoute() {
  const ctx = useContext(ActiveRouteContext);
  if (!ctx) throw new Error("useActiveRoute must be used within ActiveRouteProvider");
  return ctx;
}
