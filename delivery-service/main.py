"""delivery-service: расчёт срока доставки по районам Караганды (учебные значения)."""
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Дәріхана — жеткізу қызметі", version="1.0.0")

# Условные демонстрационные сроки (в днях), не реальные данные
DISTRICTS: dict[str, int] = {
    "Қазыбек би ауданы": 1,
    "Әлихан Бөкейхан ауданы": 2,
    "Оңтүстік-Шығыс шағынауданы": 1,
    "Майқұдық": 2,
    "Пришахтинск": 3,
    "Сортировка": 3,
}


def _find(district: str) -> str | None:
    key = district.strip().lower()
    for name in DISTRICTS:
        if name.lower() == key:
            return name
    return None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/delivery/districts")
def districts():
    return [{"district": name, "days": days} for name, days in DISTRICTS.items()]


@app.get("/delivery/estimate")
def estimate(district: str = Query(..., min_length=1, description="Аудан атауы")):
    name = _find(district)
    if name is None:
        raise HTTPException(status_code=404, detail=f"«{district}» ауданы табылмады")
    return {"district": name, "days": DISTRICTS[name]}
