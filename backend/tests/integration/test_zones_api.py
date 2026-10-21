"""zones-router -> services.zones -> datalag.zone_cache, and /ws/zones <- zone_updates."""
import time

from app.api.zones import updates as zone_updates
from app.datalag import zone_cache
from tests.factories import municipality, square


def test_zones_filtered_by_bbox_and_pieces_get_unique_ids(client, monkeypatch):
    monkeypatch.setattr(zone_cache, "_zones", [
        municipality("aarhus", 3.2, square(10.1, 56.1)),
        municipality("samsø", 6.0, square(10.5, 55.8)),
        municipality("samsø", 6.0, square(10.6, 55.9)),  # disconnected island piece
        municipality("københavn", 4.0, square(12.5, 55.6)),
    ])
    result = client.get("/api/zones", params={"bbox": "10.0,55.7,10.8,56.3"}).json()
    assert [z["id"] for z in result] == ["aarhus", "samsø", "samsø-2"]
    assert result[0]["safety_label"] == "unsafe"


def test_zones_empty_when_cache_not_loaded(client, monkeypatch):
    monkeypatch.setattr(zone_cache, "_zones", [])
    assert client.get("/api/zones", params={"bbox": "8,54,15,58"}).json() == []


def test_malformed_bbox_is_422(client):
    assert client.get("/api/zones", params={"bbox": "1,2,3"}).status_code == 422


def test_ws_zones_forwards_published_events(client):
    with client.websocket_connect("/ws/zones") as ws:
        # The handler runs on the session's own event loop; publish there once subscribed.
        for _ in range(100):
            if zone_updates.subscriber_count():
                break
            time.sleep(0.01)
        ws.portal.call(zone_updates.publish, {"type": "zones_refreshed", "zones_cached": 1})
        assert ws.receive_json() == {"type": "zones_refreshed", "zones_cached": 1}
