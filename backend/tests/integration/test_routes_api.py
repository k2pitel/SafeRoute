"""routes-router -> services.routing -> external.osrm (mocked transport), incl. the NF7 fallback."""
import httpx

from app.external import osrm

FROM, TO = "56.15,10.20", "56.16,10.22"


def _patch_osrm(monkeypatch, handler):
    real_client = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        return real_client(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(osrm.httpx, "AsyncClient", fake_client)


def _osrm_route(duration, distance):
    geometry = {"type": "LineString", "coordinates": [[10.2, 56.15], [10.22, 56.16]]}
    return {"duration": duration, "distance": distance, "geometry": geometry}


def test_osrm_request_shape_and_ranking(client, monkeypatch):
    seen = {}

    def handler(request):
        seen["url"] = request.url
        osrm_routes = [_osrm_route(1500, 2100), _osrm_route(1200, 1900), _osrm_route(1800, 2400)]
        return httpx.Response(200, json={"routes": osrm_routes})

    _patch_osrm(monkeypatch, handler)
    result = client.get("/api/routes", params={"from": FROM, "to": TO}).json()

    assert seen["url"].path.endswith("/route/v1/foot/10.2,56.15;10.22,56.16")  # OSRM wants lon,lat
    assert seen["url"].params["alternatives"] == "true"
    assert [r["duration_minutes"] for r in result] == [20, 25, 30]  # fastest first
    assert [r["safety_score"] for r in result] == [4.2, 8.6, 6.5]
    assert all(r["explanation"] for r in result)  # NF8


def test_osrm_down_falls_back(client, monkeypatch):
    def handler(request):
        raise httpx.ConnectError("OSRM unreachable")

    _patch_osrm(monkeypatch, handler)
    resp = client.get("/api/routes", params={"from": FROM, "to": TO})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_osrm_no_route_falls_back(client, monkeypatch):
    _patch_osrm(monkeypatch, lambda request: httpx.Response(200, json={"routes": []}))
    assert len(client.get("/api/routes", params={"from": FROM, "to": TO}).json()) == 2


def test_malformed_point_is_422(client):
    assert client.get("/api/routes", params={"from": "56.15", "to": TO}).status_code == 422
