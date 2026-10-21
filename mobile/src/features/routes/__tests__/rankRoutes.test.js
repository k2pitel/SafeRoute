import { rankRoutes, sortForProfile } from "../rankRoutes";

const route = (id, duration_minutes, safety_score) => ({ id, duration_minutes, safety_score });
const FAST = route("fast", 30, 4.2);
const SAFE = route("safe", 34, 8.6); // 13 % slower, 4.4 points safer
const DETOUR = route("detour", 45, 9.0); // 50 % slower, 4.8 points safer

describe("rankRoutes (UC1 step 5)", () => {
  it("time: fastest first", () => {
    expect(rankRoutes([SAFE, DETOUR, FAST], "time").map((r) => r.id)).toEqual(["fast", "safe", "detour"]);
  });

  it("safety: safest first", () => {
    expect(rankRoutes([FAST, SAFE, DETOUR], "safety").map((r) => r.id)).toEqual(["detour", "safe", "fast"]);
  });

  it("balanced: a little extra time is worth a lot of safety, a big detour isn't", () => {
    // fast 4.2; safe 8.6 - 1.33 = 7.27; detour 9.0 - 5 = 4.0
    expect(rankRoutes([FAST, DETOUR, SAFE], "balanced").map((r) => r.id)).toEqual(["safe", "fast", "detour"]);
  });

  it("does not mutate its input", () => {
    const input = [SAFE, FAST];
    rankRoutes(input, "time");
    expect(input).toEqual([SAFE, FAST]);
  });
});

describe("sortForProfile (F6)", () => {
  it("maps each risk profile to a default ranking", () => {
    expect(sortForProfile("fast")).toBe("time");
    expect(sortForProfile("balanced")).toBe("balanced");
    expect(sortForProfile("safest")).toBe("safety");
    expect(sortForProfile(undefined)).toBe("balanced");
  });
});
