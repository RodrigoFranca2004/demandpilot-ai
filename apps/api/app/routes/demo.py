from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.planning import (
    DEFAULT_FORECAST_HORIZON,
    DEFAULT_INVENTORY_HORIZON,
    planning_today,
)
from app.demo_data import RESTAURANT_NAME, refresh_demo_sales
from app.models import Restaurant
from app.schemas.demo import DemoRefreshResponse, DemoSettingsResponse

router = APIRouter(prefix="/demo", tags=["Demo"])

DEMO_RESTAURANT = select(Restaurant.id).where(Restaurant.name == RESTAURANT_NAME)


@router.get("", response_model=DemoSettingsResponse)
def get_demo_settings(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DemoSettingsResponse:
    return DemoSettingsResponse(
        restaurant_id=session.scalar(DEMO_RESTAURANT),
        planning_date=planning_today(),
        forecast_horizon=DEFAULT_FORECAST_HORIZON,
        inventory_horizon=DEFAULT_INVENTORY_HORIZON,
        refresh_enabled=settings.demo_refresh_enabled,
    )


@router.post("/sales/refresh", response_model=DemoRefreshResponse)
def refresh_sales(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DemoRefreshResponse:
    if not settings.demo_refresh_enabled:
        raise HTTPException(status_code=403, detail="Demo refresh is disabled")

    # Serialize refreshes for this restaurant until the transaction commits.
    restaurant_id = session.scalar(DEMO_RESTAURANT.with_for_update())
    if restaurant_id is None:
        raise HTTPException(status_code=404, detail="Run the initial demo seed first")

    today = planning_today()
    try:
        added_sales = refresh_demo_sales(
            session, restaurant_id, today - timedelta(days=1)
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    session.commit()
    return DemoRefreshResponse(planning_date=today, added_sales=added_sales)
