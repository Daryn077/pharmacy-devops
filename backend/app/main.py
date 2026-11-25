from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Дәріхана API — 5-нұсқа",
    description="Аптека backend: API → BLL → DAL, деректер жадта (in-memory) сақталады.",
    version="1.0.0",
)
app.include_router(router)
