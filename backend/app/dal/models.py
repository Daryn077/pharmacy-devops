"""Модели данных, которые хранит DAL."""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Medicine:
    id: int
    name: str
    price: float
    quantity: int
    prescription: bool


@dataclass
class OrderItem:
    medicine_id: int
    name: str
    price: float
    qty: int

    @property
    def subtotal(self) -> float:
        return self.price * self.qty


@dataclass
class Order:
    id: int
    items: list[OrderItem]
    has_prescription: bool
    total: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
