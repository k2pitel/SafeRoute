import { jitterCoordinate } from "../jitterCoordinate";

const AARHUS = { latitude: 56.1629, longitude: 10.2039 };

// Rough metres between two nearby points (equirectangular approximation).
function metres(a, b) {
  const k = 111_320;
  const dx = (b.longitude - a.longitude) * k * Math.cos((a.latitude * Math.PI) / 180);
  const dy = (b.latitude - a.latitude) * k;
  return Math.hypot(dx, dy);
}

describe("jitterCoordinate (news pins)", () => {
  it("is deterministic per seed", () => {
    expect(jitterCoordinate("https://x.dk/1", AARHUS.latitude, AARHUS.longitude)).toEqual(
      jitterCoordinate("https://x.dk/1", AARHUS.latitude, AARHUS.longitude)
    );
  });

  it("spreads different stories to different spots", () => {
    const a = jitterCoordinate("https://x.dk/1", AARHUS.latitude, AARHUS.longitude);
    const b = jitterCoordinate("https://x.dk/2", AARHUS.latitude, AARHUS.longitude);
    expect(a).not.toEqual(b);
  });

  it("stays roughly 450 m - 1.1 km from the town centre", () => {
    for (let i = 0; i < 200; i++) {
      const d = metres(AARHUS, jitterCoordinate(`https://x.dk/${i}`, AARHUS.latitude, AARHUS.longitude));
      expect(d).toBeGreaterThan(400);
      expect(d).toBeLessThan(1150);
    }
  });
});
