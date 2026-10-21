// Design tokens — the single source for colour, spacing, shape and type.
// Screens and ui/ components style themselves from these instead of
// hard-coding values, so the look stays consistent and changes in one place.

export const colors = {
  primary: "#007AFF",
  primaryDisabled: "#a9c9ef",
  danger: "#E5484D",
  safe: "#0EA47A",

  // Map markers (F8): one colour per data source.
  marker: {
    incident: "red",
    report: "orange",
    news: "blue",
    destination: "#007AFF",
  },

  // F7: zone polygons by safety label ("safe" stays uncoloured).
  zone: {
    unsafe: { fill: "rgba(229,72,77,0.22)", stroke: "rgba(229,72,77,0.7)" },
    mixed: { fill: "rgba(245,166,35,0.18)", stroke: "rgba(245,166,35,0.6)" },
  },

  text: "#222",
  textStrong: "#333",
  textBody: "#444",
  textMuted: "#666",
  textSubtle: "#888",
  textFaint: "#999",
  onPrimary: "white",

  surface: "white",
  surfaceMuted: "#f0f0f0",
  surfaceInfo: "#f5f7ff",
  border: "#ccc",
  borderLight: "#ddd",
  divider: "#eee",
  dividerLight: "#f0f0f0",
  backdrop: "rgba(0,0,0,0.4)",

  warningSurface: "#FFF3CD",
  warningText: "#664D03",
};

export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 20 };

export const radius = { sm: 8, md: 10, lg: 12, sheet: 16, pill: 20, fab: 24 };

export const typography = {
  title: { fontSize: 18, fontWeight: "bold" },
  heading: { fontSize: 16, fontWeight: "bold" },
  body: { fontSize: 15 },
  caption: { fontSize: 13 },
  small: { fontSize: 12 },
  sectionLabel: { fontSize: 13, color: colors.textSubtle, textTransform: "uppercase" },
};

// Floating elements (cards, FABs, dropdowns) on top of the map.
export const elevation = {
  elevation: 4,
  shadowColor: "#000",
  shadowOpacity: 0.2,
  shadowRadius: 6,
};

// Shared look of every text field.
export const inputStyle = {
  borderWidth: 1,
  borderColor: colors.border,
  borderRadius: radius.sm,
  padding: 10,
};
