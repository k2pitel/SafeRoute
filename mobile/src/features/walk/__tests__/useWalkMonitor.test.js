import { routeBbox } from "../useWalkMonitor";

jest.mock("expo-notifications", () => ({ setNotificationHandler: jest.fn() }));

describe("routeBbox (walk monitor zone fetch)", () => {
  it("covers the whole route plus a margin", () => {
    expect(routeBbox([[10.2, 56.15], [10.25, 56.1]], 0.01)).toBe(
      [10.19, 56.09, 10.26, 56.16].map((v) => String(v)).join(",")
    );
  });
});
