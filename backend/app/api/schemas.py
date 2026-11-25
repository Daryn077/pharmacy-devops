"""Pydantic-схемы запросов и ответов."""
from datetime import datetime

from pydantic import BaseModel, Field


class MedicineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["Paracetamol"])
    price: float = Field(gt=0, examples=[1500])
    quantity: int = Field(ge=0, examples=[20])
    prescription: bool = Field(default=False, examples=[False])


class MedicineOut(BaseModel):
    id: int
    name: str
    price: float
    quantity: int
    prescription: bool
    in_stock: bool


class StockChange(BaseModel):
    delta: int = Field(examples=[-2])


class OrderItemIn(BaseModel):
    medicine_id: int = Field(examples=[1])
    qty: int = Field(gt=0, examples=[2])


class OrderCreate(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1)
    has_prescription: bool = False


class OrderItemOut(BaseModel):
    medicine_id: int
    name: str
    price: float
    qty: int
    subtotal: float


class OrderOut(BaseModel):
    id: int
    items: list[OrderItemOut]
    has_prescription: bool
    total: float
    created_at: datetime


class HealthOut(BaseModel):
    status: str
