"""Business Logic Layer: правила аптеки. Работает только через интерфейсы репозиториев DAL."""
from dataclasses import dataclass

from app.bll.errors import (
    InsufficientStockError,
    InvalidOperationError,
    NotFoundError,
    PrescriptionRequiredError,
)
from app.dal import (
    InMemoryMedicineRepository,
    InMemoryOrderRepository,
    Medicine,
    MedicineRepository,
    Order,
    OrderItem,
    OrderRepository,
)


@dataclass
class OrderLine:
    medicine_id: int
    qty: int


class PharmacyService:
    def __init__(self, medicines: MedicineRepository, orders: OrderRepository):
        self._medicines = medicines
        self._orders = orders

    # ---------- Лекарства ----------
    def list_medicines(self, in_stock: bool | None = None) -> list[Medicine]:
        items = self._medicines.list()
        if in_stock is True:
            items = [m for m in items if m.quantity > 0]
        elif in_stock is False:
            items = [m for m in items if m.quantity == 0]
        return items

    def add_medicine(self, name: str, price: float, quantity: int, prescription: bool) -> Medicine:
        name = name.strip()
        if not name:
            raise InvalidOperationError("Дәрі атауы бос болмауы керек")
        if price <= 0:
            raise InvalidOperationError("Баға 0-ден үлкен болуы керек")
        if quantity < 0:
            raise InvalidOperationError("Қалдық теріс бола алмайды")
        return self._medicines.add(name, price, quantity, prescription)

    def change_stock(self, medicine_id: int, delta: int) -> Medicine:
        medicine = self._get_medicine(medicine_id)
        new_quantity = medicine.quantity + delta
        if new_quantity < 0:
            raise InvalidOperationError(
                f"Қалдық теріс бола алмайды: қазір {medicine.quantity}, өзгеріс {delta}"
            )
        return self._medicines.set_quantity(medicine_id, new_quantity)

    # ---------- Заказы ----------
    @staticmethod
    def calculate_total(items: list[OrderItem]) -> float:
        return round(sum(item.price * item.qty for item in items), 2)

    def create_order(self, lines: list[OrderLine], has_prescription: bool) -> Order:
        if not lines:
            raise InvalidOperationError("Тапсырыста кемінде бір позиция болуы керек")

        # Повторяющиеся medicine_id объединяем в одну позицию
        requested: dict[int, int] = {}
        for line in lines:
            if line.qty <= 0:
                raise InvalidOperationError("Саны 0-ден үлкен болуы керек")
            requested[line.medicine_id] = requested.get(line.medicine_id, 0) + line.qty

        # 1) Сначала проверяем ВСЕ позиции, ничего не изменяя
        items: list[OrderItem] = []
        for medicine_id, qty in requested.items():
            medicine = self._get_medicine(medicine_id)
            if medicine.prescription and not has_prescription:
                raise PrescriptionRequiredError(f"«{medicine.name}» тек рецептпен сатылады")
            if medicine.quantity < qty:
                raise InsufficientStockError(
                    f"«{medicine.name}» жеткіліксіз: қалдық {medicine.quantity}, сұралды {qty}"
                )
            items.append(OrderItem(medicine.id, medicine.name, medicine.price, qty))

        # 2) Только после успешной проверки уменьшаем остатки
        for item in items:
            medicine = self._get_medicine(item.medicine_id)
            self._medicines.set_quantity(item.medicine_id, medicine.quantity - item.qty)

        return self._orders.add(items, has_prescription, self.calculate_total(items))

    def get_order(self, order_id: int) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise NotFoundError(f"#{order_id} тапсырысы табылмады")
        return order

    def _get_medicine(self, medicine_id: int) -> Medicine:
        medicine = self._medicines.get(medicine_id)
        if medicine is None:
            raise NotFoundError(f"#{medicine_id} дәрісі табылмады")
        return medicine


def create_default_service() -> PharmacyService:
    """Сборка сервиса с in-memory репозиториями (используется приложением)."""
    return PharmacyService(InMemoryMedicineRepository(), InMemoryOrderRepository())
