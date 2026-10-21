import { dedupe, searchPlaces } from "../geocoding";

beforeEach(() => {
  global.fetch = jest.fn();
});

describe("dedupe", () => {
  it("drops places with the same primary + secondary label, case-insensitively", () => {
    const places = [
      { primary: "Nørregade", secondary: "Aarhus, Denmark" },
      { primary: "nørregade", secondary: "aarhus, denmark" },
      { primary: "Nørregade", secondary: "København, Denmark" },
    ];
    expect(dedupe(places)).toHaveLength(2);
  });
});

describe("searchPlaces", () => {
  it("doesn't query Nominatim for fewer than 2 characters", async () => {
    expect(await searchPlaces("a")).toEqual([]);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("maps, dedupes and limits results", async () => {
    const item = (id, road) => ({
      place_id: id,
      display_name: `${road}, Aarhus, Denmark`,
      lat: "56.15",
      lon: "10.2",
      address: { road, city: "Aarhus", country: "Denmark" },
    });
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [item(1, "Nørregade"), item(2, "Nørregade"), item(3, "Vestergade")],
    });
    const places = await searchPlaces("gade", { limit: 6 });
    expect(places.map((p) => p.primary)).toEqual(["Nørregade", "Vestergade"]);
    expect(places[0]).toMatchObject({ latitude: 56.15, longitude: 10.2, secondary: "Aarhus, Denmark" });
  });

  it("throws a readable error instead of hiding a blocked request (ch. 6, I1.1)", async () => {
    global.fetch.mockResolvedValueOnce({ ok: false, status: 403 });
    await expect(searchPlaces("Aarhus H")).rejects.toThrow("HTTP 403");
  });

  it("identifies the app to Nominatim", async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => [] });
    await searchPlaces("Aarhus");
    expect(global.fetch.mock.calls[0][1].headers["User-Agent"]).toMatch(/SafeRoute/);
  });
});
