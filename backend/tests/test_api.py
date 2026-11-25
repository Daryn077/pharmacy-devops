"""API-тесты через FastAPI TestClient. Каждый тест получает свой чистый сервис."""
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_pharmacy_service
from app.bll import PharmacyService
from app.dal import InMemoryMedicineRepository, InMemoryOrderRepository
from app.main import app


@pytest.fixture
def client():
    medicines = InMemoryMedicineRepository(seed=False)
    medicines.add("Paracetamol", 1500, 20, False)   # id=1
    medicines.add("Amoxicillin", 2500, 5, True)     # id=2
    medicines.add("Omeprazole", 1200, 0, False)     # id=3
    service = PharmacyService(medicines, InMemoryOrderRepository())
    app.dependency_overrides[get_pharmacy_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_medicines(client):
    r = client.get("/medicines")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_list_in_stock_only(client):
    r = client.get("/medicines?in_stock=true")
    assert [m["name"] for m in r.json()] == ["Paracetamol", "Amoxicillin"]


def test_add_medicine(client):
    body = {"name": "Ibuprofen", "price": 800, "quantity": 10, "prescription": False}
    r = client.post("/medicines", json=body)
    assert r.status_code == 201
    assert r.json()["id"] == 4
    assert r.json()["name"] == "Ibuprofen"


def test_patch_stock_decrease(client):
    r = client.patch("/medicines/1/stock", json={"delta": -2})
    assert r.status_code == 200
    assert r.json()["quantity"] == 18


def test_patch_stock_negative_returns_400(client):
    r = client.patch("/medicines/1/stock", json={"delta": -21})
    assert r.status_code == 400


def test_create_order_and_total(client):
    r = client.post("/orders", json={"items": [{"medicine_id": 1, "qty": 2}], "has_prescription": False})
    assert r.status_code == 201
    assert r.json()["total"] == 3000
    assert client.get("/medicines").json()[0]["quantity"] == 18


def test_prescription_required_returns_403(client):
    r = client.post("/orders", json={"items": [{"medicine_id": 2, "qty": 1}], "has_prescription": False})
    assert r.status_code == 403


def test_with_prescription_ok(client):
    r = client.post("/orders", json={"items": [{"medicine_id": 2, "qty": 1}], "has_prescription": True})
    assert r.status_code == 201
    assert r.json()["total"] == 2500


def test_insufficient_stock_returns_409(client):
    r = client.post("/orders", json={"items": [{"medicine_id": 1, "qty": 21}]})
    assert r.status_code == 409


def test_get_order(client):
    created = client.post("/orders", json={"items": [{"medicine_id": 1, "qty": 3}]}).json()
    r = client.get(f"/orders/{created['id']}")
    assert r.status_code == 200
    assert r.json()["total"] == 4500


def test_not_found_returns_404(client):
    assert client.get("/orders/999").status_code == 404
    assert client.patch("/medicines/999/stock", json={"delta": 1}).status_code == 404
    assert client.post("/orders", json={"items": [{"medicine_id": 999, "qty": 1}]}).status_code == 404
