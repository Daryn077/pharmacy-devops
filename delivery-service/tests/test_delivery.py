from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_estimate_known_district():
    r = client.get("/delivery/estimate", params={"district": "Қазыбек би ауданы"})
    assert r.status_code == 200
    assert r.json()["days"] == 1


def test_estimate_unknown_district():
    assert client.get("/delivery/estimate", params={"district": "Астана"}).status_code == 404
