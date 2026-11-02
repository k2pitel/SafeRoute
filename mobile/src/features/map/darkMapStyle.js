// Google Maps style for dark mode (Android). iOS/Apple Maps is switched with
// MapView's userInterfaceStyle prop instead, which ignores this.
export const DARK_MAP_STYLE = [
  { elementType: "geometry", stylers: [{ color: "#1d2233" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#8d94a8" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#141826" }] },
  { featureType: "administrative", elementType: "geometry", stylers: [{ color: "#3a4260" }] },
  { featureType: "administrative.locality", elementType: "labels.text.fill", stylers: [{ color: "#c3c9d9" }] },
  { featureType: "poi", elementType: "labels.text.fill", stylers: [{ color: "#7f879c" }] },
  { featureType: "poi.park", elementType: "geometry", stylers: [{ color: "#1a2b2a" }] },
  { featureType: "poi.park", elementType: "labels.text.fill", stylers: [{ color: "#5d8a7a" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#2c3348" }] },
  { featureType: "road", elementType: "geometry.stroke", stylers: [{ color: "#1a1f30" }] },
  { featureType: "road", elementType: "labels.text.fill", stylers: [{ color: "#9aa1b5" }] },
  { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#3b4466" }] },
  { featureType: "road.highway", elementType: "geometry.stroke", stylers: [{ color: "#1f2538" }] },
  { featureType: "road.highway", elementType: "labels.text.fill", stylers: [{ color: "#c3c9d9" }] },
  { featureType: "transit", elementType: "geometry", stylers: [{ color: "#262d42" }] },
  { featureType: "transit.station", elementType: "labels.text.fill", stylers: [{ color: "#9aa1b5" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#0f1424" }] },
  { featureType: "water", elementType: "labels.text.fill", stylers: [{ color: "#4e5670" }] },
];
