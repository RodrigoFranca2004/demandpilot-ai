from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.planning import DEFAULT_FORECAST_HORIZON
from app.forecasting.service import (
    ForecastReport,
    forecast_product_demand,
)
from app.models import Product
from app.schemas.forecasting import (
    ForecastMetricsResponse,
    ForecastResponse,
)

router = APIRouter(
    prefix="/products",
    tags=["Forecasting"],
)


def get_forecast_report(
    db: Session,
    product_id: int,
    horizon: int = DEFAULT_FORECAST_HORIZON,
) -> ForecastReport:
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    try:
        return forecast_product_demand(
            session=db,
            product_id=product_id,
            horizon=horizon,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.get(
    "/{product_id}/forecast",
    response_model=ForecastResponse,
)
def get_product_forecast(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    horizon: Annotated[int, Query(ge=1, le=30)] = DEFAULT_FORECAST_HORIZON,
) -> ForecastResponse:
    report = get_forecast_report(
        db=db,
        product_id=product_id,
        horizon=horizon,
    )

    return ForecastResponse.model_validate(report)


@router.get(
    "/{product_id}/forecast/metrics",
    response_model=ForecastMetricsResponse,
)
def get_product_forecast_metrics(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ForecastMetricsResponse:
    report = get_forecast_report(
        db=db,
        product_id=product_id,
        horizon=1,
    )

    return ForecastMetricsResponse.model_validate(report)
