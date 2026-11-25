"""Data Access Layer: репозитории, которые хранят данные в оперативной памяти."""
from abc import ABC, abstractmethod
from copy import deepcopy

from app.dal.models import Medicine, Order, OrderItem


class MedicineRepository(ABC):
    @abstractmethod
    def list(self) -> list[Medicine]: ...

    @abstractmethod
    def get(self, medicine_id: int) -> Medicine | None: ...

    @abstractmethod
    def add(self, name: str, price: float, quantity: int, prescription: bool) -> Medicine: ...

    @abstractmethod
    def set_quantity(self, medicine_id: int, quantity: int) -> Medicine: ...


class OrderRepository(ABC):
    @abstractmethod
    def add(self, items: list[OrderItem], has_prescription: bool, total: float) -> Order: ...

    @abstractmethod
    def get(self, order_id: int) -> Order | None: ...


SEED_MEDICINES = [
    ("Парацетамол 500 мг", 450, 40, False),
    ("Ибупрофен 200 мг", 780, 25, False),
    ("Амоксициллин 500 мг", 2350, 12, True),
    ("Цетиризин 10 мг", 990, 18, False),
    ("Омепразол 20 мг", 1290, 0, False),
    ("Азитромицин 250 мг", 3100, 6, True),
    ("Д3 дәрумені 2000 ХБ", 2650, 30, False),
    ("Лоратадин 10 мг", 620, 3, False),
]


class InMemoryMedicineRepository(MedicineRepository):
    def __init__(self, seed: bool = True):
        self._items: dict[int, Medicine] = {}
        self._next_id = 1
        if seed:
            for name, price, quantity, prescription in SEED_MEDICINES:
                self.add(name, price, quantity, prescription)

    def list(self) -> list[Medicine]:
        return [deepcopy(m) for m in sorted(self._items.values(), key=lambda m: m.id)]

    def get(self, medicine_id: int) -> Medicine | None:
        medicine = self._items.get(medicine_id)
        return deepcopy(medicine) if medicine else None

    def add(self, name: str, price: float, quantity: int, prescription: bool) -> Medicine:
        medicine = Medicine(self._next_id, name, price, quantity, prescription)
        self._items[medicine.id] = medicine
        self._next_id += 1
        return deepcopy(medicine)

    def set_quantity(self, medicine_id: int, quantity: int) -> Medicine:
        self._items[medicine_id].quantity = quantity
        return deepcopy(self._items[medicine_id])


class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._items: dict[int, Order] = {}
        self._next_id = 1

    def add(self, items: list[OrderItem], has_prescription: bool, total: float) -> Order:
        order = Order(self._next_id, items, has_prescription, total)
        self._items[order.id] = order
        self._next_id += 1
        return deepcopy(order)

    def get(self, order_id: int) -> Order | None:
        order = self._items.get(order_id)
        return deepcopy(order) if order else None
