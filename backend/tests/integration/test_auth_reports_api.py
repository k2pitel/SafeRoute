"""auth/reports routers -> services -> datalag.local_store, and reports -> Async Worker (NF5)."""
from app.config import settings
from app.shared.geo import BBox

AARHUS = {"type": "harassment", "latitude": 56.15, "longitude": 10.21, "description": "Råben og chikane"}
AARHUS_BBOX = "10.1,56.1,10.3,56.2"


def test_signup_then_duplicate_is_409(client):
    body = {"email": "Ny@Example.com", "password": "pw"}
    first = client.post("/api/auth/signup", json=body)
    assert first.status_code == 201
    assert first.json()["user"]["email"] == "ny@example.com"  # normalized
    assert client.post("/api/auth/signup", json=body).status_code == 409


def test_login_with_wrong_password_is_401(client):
    client.post("/api/auth/signup", json={"email": "a@b.dk", "password": "rigtigt"})
    assert client.post("/api/auth/login", json={"email": "a@b.dk", "password": "forkert"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "a@b.dk", "password": "rigtigt"}).status_code == 200


def test_report_requires_login(client):
    assert client.post("/api/reports", json=AARHUS).status_code == 401


def test_report_is_created_unconfirmed_and_visible_in_bbox(client, auth_header):
    created = client.post("/api/reports", json=AARHUS, headers=auth_header)
    assert created.status_code == 201
    assert created.json()["confirmations"] == 0

    listed = client.get("/api/reports", params={"bbox": AARHUS_BBOX}).json()
    assert [r["id"] for r in listed] == [created.json()["id"]]


def test_report_outside_bbox_is_not_listed(client, auth_header):
    client.post("/api/reports", json=AARHUS, headers=auth_header)
    copenhagen_bbox = "12.4,55.6,12.7,55.8"
    assert client.get("/api/reports", params={"bbox": copenhagen_bbox}).json() == []


def test_reporter_identity_is_not_exposed(client, auth_header):
    created = client.post("/api/reports", json=AARHUS, headers=auth_header).json()
    assert "user_id" not in created
    assert "user_id" not in client.get("/api/reports", params={"bbox": AARHUS_BBOX}).json()[0]


def test_confirm_by_another_user_increments_and_404s_on_unknown(client, auth_header, new_user):
    report_id = client.post("/api/reports", json=AARHUS, headers=auth_header).json()["id"]
    confirmed = client.post(f"/api/reports/{report_id}/confirm", headers=new_user())
    assert confirmed.json()["confirmations"] == 1
    assert client.post("/api/reports/9999/confirm", headers=auth_header).status_code == 404


def test_confirm_requires_login(client, auth_header):
    report_id = client.post("/api/reports", json=AARHUS, headers=auth_header).json()["id"]
    assert client.post(f"/api/reports/{report_id}/confirm").status_code == 401


def test_cannot_confirm_own_report(client, auth_header):
    """F3: verification must come from other users."""
    report_id = client.post("/api/reports", json=AARHUS, headers=auth_header).json()["id"]
    assert client.post(f"/api/reports/{report_id}/confirm", headers=auth_header).status_code == 403


def test_same_user_confirming_twice_is_409_and_not_counted(client, auth_header, new_user):
    """Ch. 6, I2.7: one user alone must not be able to make a report look verified."""
    report_id = client.post("/api/reports", json=AARHUS, headers=auth_header).json()["id"]
    other = new_user()
    assert client.post(f"/api/reports/{report_id}/confirm", headers=other).status_code == 200
    second = client.post(f"/api/reports/{report_id}/confirm", headers=other)
    assert second.status_code == 409
    listed = client.get("/api/reports", params={"bbox": AARHUS_BBOX}).json()
    assert listed[0]["confirmations"] == 1


def test_report_rate_limit_is_429(client, auth_header, monkeypatch):
    """NF10: a single user can submit at most N reports per window."""
    monkeypatch.setattr(settings, "report_rate_limit", 2)
    assert client.post("/api/reports", json=AARHUS, headers=auth_header).status_code == 201
    assert client.post("/api/reports", json=AARHUS, headers=auth_header).status_code == 201
    third = client.post("/api/reports", json=AARHUS, headers=auth_header)
    assert third.status_code == 429
    assert "Retry-After" in third.headers


def test_rate_limit_is_per_user(client, auth_header, new_user, monkeypatch):
    monkeypatch.setattr(settings, "report_rate_limit", 1)
    assert client.post("/api/reports", json=AARHUS, headers=auth_header).status_code == 201
    assert client.post("/api/reports", json=AARHUS, headers=new_user()).status_code == 201


def test_report_becoming_verified_triggers_one_recalculation(client, auth_header, new_user, async_worker, monkeypatch):
    """Afsnit 4.2.3 / NF5: the confirmation that reaches the threshold submits
    exactly one targeted recalculation for the area around the report."""
    monkeypatch.setattr(settings, "report_verification_threshold", 2)
    report_id = client.post("/api/reports", json=AARHUS, headers=auth_header).json()["id"]

    client.post(f"/api/reports/{report_id}/confirm", headers=new_user())
    assert async_worker.recalculations == []

    client.post(f"/api/reports/{report_id}/confirm", headers=new_user())
    client.post(f"/api/reports/{report_id}/confirm", headers=new_user())
    assert len(async_worker.recalculations) == 1
    area = async_worker.recalculations[0]
    assert isinstance(area, BBox)
    assert area.min_lon < AARHUS["longitude"] < area.max_lon
    assert area.min_lat < AARHUS["latitude"] < area.max_lat
