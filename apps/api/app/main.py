from fastapi import FastAPI

from app.routes.forecasting import router as forecasting_router
from app.routes.products import router as products_router

app = FastAPI(
    title="DemandPilot AI API",
    version="0.1.0",
)

app.include_router(products_router)
app.include_router(forecasting_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
