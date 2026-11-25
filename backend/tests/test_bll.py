"""Unit-тесты BLL. Настоящий репозиторий подменяется фейковым (FakeMedicineRepository)."""
import pytest

from app.bll import (
    InsufficientStockError,
    InvalidOperationError,
    NotFoundError,
    OrderLine,
    PharmacyService,
    PrescriptionRequiredError,
)
from app.dal import Medicine, MedicineRepository, Order, OrderRepository


class FakeMedicineRepository(MedicineRepository):
    def __init__(self, medicines: list[Medicine]):
        self.data = {m.id: m for m in medicines}
        self.set_quantity_calls = 0

    def list(self):
        return list(self.data.values())

    def get(self, medicine_id):
        m = self.data.get(medicine_id)
        return Medicine(**vars(m)) if m else None

    def add(self, name, price, quantity, prescription):
        m = Medicine(max(self.data, default=0) + 1, name, price, quantity, prescription)
        self.data[m.id] = m
        return m

    def set_quantity(self, medicine_id, quantity):
        self.set_quantity_calls += 1
        self.data[medicine_id].quantity = quantity
        return self.data[medicine_id]


class FakeOrderRepository(OrderRepository):
    def __init__(self):
        self.data = {}

    def add(self, items, has_prescription, total):
        order = Order(len(self.data) + 1, items, has_prescription, total)
        self.data[order.id] = order
        return order

    def get(self, order_id):
        return self.data.get(order_id)


@pytest.fixture
def repos():
    medicines = FakeMedicineRepository([
        Medicine(1, "Paracetamol", 1500, 10, False),
        Medicine(2, "Amoxicillin", 2000, 5, True),
        Medicine(3, "Omeprazole", 1000, 0, False),
    ])
    return medicines, FakeOrderRepository()


@pytest.fixture
def service(repos):
    return PharmacyService(*repos)


def test_filter_in_stock(service):
    names = [m.name for m in service.list_medicines(in_stock=True)]
    assert names == ["Paracetamol", "Amoxicillin"]


def test_stock_increase(service):
    assert service.change_stock(1, 5).quantity == 15


def test_stock_cannot_be_negative(service, repos):
    with pytest.raises(InvalidOperationError):
        service.change_stock(1, -11)
    assert repos[0].data[1].quantity == 10


def test_total_is_sum_of_price_times_qty(service):
    order = service.create_order([OrderLine(1, 2), OrderLine(2, 1)], has_prescription=True)
    assert order.total == 1500 * 2 + 2000 * 1


def test_order_decreases_stock(service, repos):
    service.create_order([OrderLine(1, 3)], has_prescription=False)
    assert repos[0].data[1].quantity == 7


def test_prescription_required(service):
    with pytest.raises(PrescriptionRequiredError):
        service.create_order([OrderLine(2, 1)], has_prescription=False)


def test_insufficient_stock(service):
    with pytest.raises(InsufficientStockError):
        service.create_order([OrderLine(1, 11)], has_prescription=False)


def test_failed_order_does_not_change_stock(service, repos):
    with pytest.raises(InsufficientStockError):
        service.create_order([OrderLine(1, 2), OrderLine(3, 1)], has_prescription=False)
    assert repos[0].data[1].quantity == 10
    assert repos[0].set_quantity_calls == 0


def test_duplicate_items_are_combined(service):
    with pytest.raises(InsufficientStockError):
        service.create_order([OrderLine(1, 6), OrderLine(1, 6)], has_prescription=False)
    order = service.create_order([OrderLine(1, 2), OrderLine(1, 3)], has_prescription=False)
    assert len(order.items) == 1 and order.items[0].qty == 5


def test_unknown_medicine_and_order(service):
    with pytest.raises(NotFoundError):
        service.change_stock(999, 1)
    with pytest.raises(NotFoundError):
        service.get_order(999)


def test_invalid_price_rejected(service):
    with pytest.raises(InvalidOperationError):
        service.add_medicine("Test", 0, 1, False)
