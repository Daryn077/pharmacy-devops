"""Получение сервиса бизнес-логики. В тестах подменяется через app.dependency_overrides."""
from app.bll import PharmacyService, create_default_service

_service: PharmacyService | None = None


def get_pharmacy_service() -> PharmacyService:
    global _service
    if _service is None:
        _service = create_default_service()
    return _service
