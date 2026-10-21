import { api, setAuthToken } from "../api";

function respond(status, body, { json = true } = {}) {
  global.fetch.mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: json ? async () => body : async () => Promise.reject(new Error("not JSON")),
  });
}

beforeEach(() => {
  global.fetch = jest.fn();
  setAuthToken(null);
});

describe("api.request error handling", () => {
  it("surfaces FastAPI's string detail", async () => {
    respond(401, { detail: "Invalid email or password" });
    await expect(api.login("a@b.dk", "x")).rejects.toThrow("Invalid email or password");
  });

  it("joins a 422 validation list into readable text", async () => {
    respond(422, { detail: [{ msg: "Field required" }, { msg: "Field required" }] });
    await expect(api.submitReport({})).rejects.toThrow("Field required; Field required");
  });

  it("falls back to the status code for non-JSON errors", async () => {
    respond(502, null, { json: false });
    await expect(api.getReports("1,2,3,4")).rejects.toThrow("API error 502");
  });
});

describe("api auth header", () => {
  it("sends the Bearer token once set, and not before", async () => {
    respond(200, []);
    await api.getReports("1,2,3,4");
    expect(global.fetch.mock.calls[0][1].headers.Authorization).toBeUndefined();

    setAuthToken("tok");
    respond(200, { id: 1 });
    await api.confirmReport(1);
    const [url, options] = global.fetch.mock.calls[1];
    expect(url).toMatch(/\/api\/reports\/1\/confirm$/);
    expect(options.method).toBe("POST");
    expect(options.headers.Authorization).toBe("Bearer tok");
  });
});
