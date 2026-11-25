"""FastAPI-роутеры. API обращается только к BLL (PharmacyService), не к DAL."""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_pharmacy_service
from app.api.schemas import (
    HealthOut,
    MedicineCreate,
    MedicineOut,
    OrderCreate,
    OrderItemOut,
    OrderOut,
    StockChange,
)
from app.bll import (
    BusinessError,
    InsufficientStockError,
    InvalidOperationError,
    NotFoundError,
    OrderLine,
    PharmacyService,
    PrescriptionRequiredError,
)

router = APIRouter()

ERROR_STATUS = {
    InvalidOperationError: status.HTTP_400_BAD_REQUEST,
    PrescriptionRequiredError: status.HTTP_403_FORBIDDEN,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    InsufficientStockError: status.HTTP_409_CONFLICT,
}


def to_http(error: BusinessError) -> HTTPException:
    return HTTPException(status_code=ERROR_STATUS.get(type(error), 400), detail=error.message)


def medicine_out(m) -> MedicineOut:
    return MedicineOut(
        id=m.id, name=m.name, price=m.price, quantity=m.quantity,
        prescription=m.prescription, in_stock=m.quantity > 0,
    )


def order_out(o) -> OrderOut:
    return OrderOut(
        id=o.id,
        items=[
            OrderItemOut(medicine_id=i.medicine_id, name=i.name, price=i.price,
                         qty=i.qty, subtotal=i.subtotal)
            for i in o.items
        ],
        has_prescription=o.has_prescription,
        total=o.total,
        created_at=o.created_at,
    )


@router.get("/health", response_model=HealthOut, tags=["health"])
def health():
    return {"status": "ok"}


@router.get("/medicines", response_model=list[MedicineOut], tags=["medicines"])
def list_medicines(
    in_stock: bool | None = Query(default=None, description="true — тек қолда барлары"),
    service: PharmacyService = Depends(get_pharmacy_service),
):
    return [medicine_out(m) for m in service.list_medicines(in_stock)]


@router.post("/medicines", response_model=MedicineOut, status_code=201, tags=["medicines"])
def add_medicine(body: MedicineCreate, service: PharmacyService = Depends(get_pharmacy_service)):
    try:
        return medicine_out(service.add_medicine(body.name, body.price, body.quantity, body.prescription))
    except BusinessError as e:
        raise to_http(e)


@router.patch("/medicines/{medicine_id}/stock", response_model=MedicineOut, tags=["medicines"])
def change_stock(medicine_id: int, body: StockChange,
                 service: PharmacyService = Depends(get_pharmacy_service)):
    try:
        return medicine_out(service.change_stock(medicine_id, body.delta))
    except BusinessError as e:
        raise to_http(e)


@router.post("/orders", response_model=OrderOut, status_code=201, tags=["orders"])
def create_order(body: OrderCreate, service: PharmacyService = Depends(get_pharmacy_service)):
    try:
        lines = [OrderLine(i.medicine_id, i.qty) for i in body.items]
        return order_out(service.create_order(lines, body.has_prescription))
    except BusinessError as e:
        raise to_http(e)


@router.get("/orders/{order_id}", response_model=OrderOut, tags=["orders"])
def get_order(order_id: int, service: PharmacyService = Depends(get_pharmacy_service)):
    try:
        return order_out(service.get_order(order_id))
    except BusinessError as e:
        raise to_http(e)
