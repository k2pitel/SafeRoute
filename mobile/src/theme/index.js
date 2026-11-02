// Design tokens — the single source for colour, spacing, shape and type.
// Screens and ui/ components style themselves from these instead of
// hard-coding values, so the look stays consistent and changes in one place.
//
// Colours come in a light and a dark palette. Components read the active
// one through useTheme() / useThemedStyles(), so switching (system setting
// or Settings → Appearance) restyles the app live.
import { createContext, useContext, useMemo } from "react";
import { useColorScheme } from "react-native";

const shared = {
  // Map markers (F8): one colour per data source.
  marker: {
    incident: "red",
    report: "orange",
    news: "blue",
    destination: "#3B5BDB",
  },
  // F7: zone polygons by safety label ("safe" stays uncoloured).
  zone: {
    unsafe: { fill: "rgba(229,72,77,0.22)", stroke: "rgba(229,72,77,0.7)" },
    mixed: { fill: "rgba(245,166,35,0.18)", stroke: "rgba(245,166,35,0.6)" },
  },
  onPrimary: "white",
};

export const lightColors = {
  ...shared,
  primary: "#3B5BDB",
  primaryDark: "#2B44B0",
  primarySoft: "#E8EDFF",
  primaryDisabled: "#AAB8EE",
  danger: "#E5484D",
  dangerSoft: "#FDECEC",
  warning: "#E8890C",
  warningSoft: "#FFF4E0",
  safe: "#0EA47A",
  safeSoft: "#E3F6EF",

  text: "#1A1F36",
  textStrong: "#2A3047",
  textBody: "#3C4257",
  textMuted: "#5E6478",
  textSubtle: "#7A8094",
  textFaint: "#9AA0B2",

  background: "#F4F6FB",
  surface: "#FFFFFF",
  surfaceMuted: "#EEF1F6",
  surfaceInfo: "#F0F3FF",
  border: "#D5DAE5",
  borderLight: "#E3E7EF",
  divider: "#ECEFF4",
  dividerLight: "#F1F3F7",
  backdrop: "rgba(16,20,40,0.45)",

  warningSurface: "#FFF3CD",
  warningText: "#664D03",
};

export const darkColors = {
  ...shared,
  marker: { ...shared.marker, destination: "#5C7CFA" },
  primary: "#5C7CFA",
  primaryDark: "#B4C3FF", // text on primarySoft: light in dark mode
  primarySoft: "#1F2A55",
  primaryDisabled: "#34407A",
  danger: "#FF6B6E",
  dangerSoft: "#3A1D24",
  warning: "#F5A524",
  warningSoft: "#3A2C14",
  safe: "#2FD39B",
  safeSoft: "#11342A",

  text: "#E8EBF4",
  textStrong: "#D6DAE6",
  textBody: "#BEC3D2",
  textMuted: "#9AA1B5",
  textSubtle: "#7F879C",
  textFaint: "#646C82",

  background: "#0E1220",
  surface: "#181D2E",
  surfaceMuted: "#232A3F",
  surfaceInfo: "#1C2340",
  border: "#3A4260",
  borderLight: "#2A3148",
  divider: "#262D42",
  dividerLight: "#21283B",
  backdrop: "rgba(0,0,0,0.6)",

  warningSurface: "#3A2C14",
  warningText: "#F5C76B",
};

export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 20, xxl: 28 };

export const radius = { sm: 10, md: 12, lg: 16, sheet: 20, pill: 999, fab: 28 };

// Everything that depends on the palette, built once per palette.
export function makeTheme(colors, dark) {
  const typography = {
    display: { fontSize: 30, fontWeight: "800", color: colors.text },
    title: { fontSize: 20, fontWeight: "700", color: colors.text },
    heading: { fontSize: 16, fontWeight: "700", color: colors.text },
    body: { fontSize: 15, color: colors.textBody },
    caption: { fontSize: 13 },
    small: { fontSize: 12 },
    sectionLabel: {
      fontSize: 12,
      fontWeight: "700",
      letterSpacing: 0.8,
      color: colors.textSubtle,
      textTransform: "uppercase",
    },
  };

  // Floating elements (cards, FABs, dropdowns) on top of the map.
  const elevation = {
    elevation: 5,
    shadowColor: "#000",
    shadowOpacity: dark ? 0.5 : 0.16,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
  };

  // Resting cards in lists (news, settings groups, metrics). Shadows barely
  // show on a dark background, so dark cards get a hairline border instead.
  const cardShadow = {
    elevation: dark ? 0 : 2,
    shadowColor: "#1A1F36",
    shadowOpacity: dark ? 0 : 0.07,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
  };

  const card = {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: dark ? 1 : 0,
    borderColor: colors.borderLight,
    ...cardShadow,
  };

  // Shared look of every text field.
  const inputStyle = {
    borderWidth: 1,
    borderColor: colors.borderLight,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingHorizontal: 14,
    paddingVertical: 11,
    fontSize: 15,
    color: colors.text,
  };

  // Low / Moderate / High → tint (used by crime index metrics).
  const levelColors = (level) => {
    if (level === "High") return { fg: colors.danger, bg: colors.dangerSoft };
    if (level === "Moderate") return { fg: colors.warning, bg: colors.warningSoft };
    return { fg: colors.safe, bg: colors.safeSoft };
  };

  return { dark, colors, typography, elevation, cardShadow, card, inputStyle, levelColors, spacing, radius };
}

const lightTheme = makeTheme(lightColors, false);
const darkTheme = makeTheme(darkColors, true);

const ThemeContext = createContext(lightTheme);

// preference: "system" | "light" | "dark" (Settings → Appearance).
export function ThemeProvider({ preference = "system", children }) {
  const system = useColorScheme();
  const dark = preference === "dark" || (preference === "system" && system === "dark");
  return <ThemeContext.Provider value={dark ? darkTheme : lightTheme}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  return useContext(ThemeContext);
}

// `factory(theme)` → StyleSheet; rebuilt only when the theme changes.
// Define the factory at module level so it is stable between renders.
export function useThemedStyles(factory) {
  const theme = useTheme();
  return useMemo(() => factory(theme), [theme, factory]);
}
