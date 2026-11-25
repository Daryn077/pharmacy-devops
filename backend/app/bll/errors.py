"""Ошибки бизнес-логики. API-слой переводит их в HTTP-статусы."""


class BusinessError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidOperationError(BusinessError):
    """Недопустимая операция (например, отрицательный остаток) -> 400."""


class PrescriptionRequiredError(BusinessError):
    """Нужен рецепт -> 403."""


class NotFoundError(BusinessError):
    """Лекарство или заказ не найдены -> 404."""


class InsufficientStockError(BusinessError):
    """Недостаточно товара -> 409."""
