jest.mock("expo-notifications", () => ({ setNotificationHandler: jest.fn() }));

import { isInsidePolygon, zonesToGeofences } from "../geofence";

const square = (lon, lat, size = 1) => [
  [
    [lon, lat],
    [lon + size, lat],
    [lon + size, lat + size],
    [lon, lat + size],
    [lon, lat],
  ],
];

describe("isInsidePolygon (F5 zone condition)", () => {
  const polygon = [
    { latitude: 56, longitude: 10 },
    { latitude: 56, longitude: 11 },
    { latitude: 57, longitude: 11 },
    { latitude: 57, longitude: 10 },
  ];

  it("detects a point inside", () => {
    expect(isInsidePolygon({ latitude: 56.5, longitude: 10.5 }, polygon)).toBe(true);
  });

  it("rejects points outside, also just past an edge", () => {
    expect(isInsidePolygon({ latitude: 57.5, longitude: 10.5 }, polygon)).toBe(false);
    expect(isInsidePolygon({ latitude: 56.5, longitude: 11.0001 }, polygon)).toBe(false);
  });

  it("handles a concave (L-shaped) polygon", () => {
    const lShape = [
      { latitude: 0, longitude: 0 },
      { latitude: 0, longitude: 2 },
      { latitude: 1, longitude: 2 },
      { latitude: 1, longitude: 1 },
      { latitude: 2, longitude: 1 },
      { latitude: 2, longitude: 0 },
    ];
    expect(isInsidePolygon({ latitude: 0.5, longitude: 1.5 }, lShape)).toBe(true);
    expect(isInsidePolygon({ latitude: 1.5, longitude: 1.5 }, lShape)).toBe(false); // the notch
  });
});

describe("zonesToGeofences (GET /api/zones -> geofence adapter)", () => {
  const zones = [
    { id: "aarhus", safety_label: "unsafe", geometry: { type: "Polygon", coordinates: square(10, 56) } },
    { id: "samsø", safety_label: "unsafe", geometry: { type: "MultiPolygon", coordinates: [square(20, 50), square(30, 50)] } },
    { id: "odense", safety_label: "safe", geometry: { type: "Polygon", coordinates: square(0, 0) } },
  ];

  it("keeps only the requested labels and splits MultiPolygons", () => {
    expect(zonesToGeofences(zones).map((z) => z.id)).toEqual(["aarhus", "samsø#0", "samsø#1"]);
  });

  it("flips GeoJSON [lon, lat] into {latitude, longitude} and keeps the label", () => {
    const [aarhus] = zonesToGeofences(zones);
    expect(aarhus.label).toBe("unsafe");
    expect(aarhus.polygon[1]).toEqual({ latitude: 56, longitude: 11 });
  });

  it("can include other labels", () => {
    expect(zonesToGeofences(zones, { labels: ["safe"] }).map((z) => z.id)).toEqual(["odense"]);
  });
});
