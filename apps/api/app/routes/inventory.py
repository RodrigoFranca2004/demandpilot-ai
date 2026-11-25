from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.planning import DEFAULT_INVENTORY_HORIZON
from app.inventory.service import analyze_inventory
from app.models import Restaurant
from app.schemas.inventory import InventoryAnalysisResponse

router = APIRouter(
    prefix="/restaurants",
    tags=["Inventory"],
)


@router.get(
    "/{restaurant_id}/inventory/analysis",
    response_model=InventoryAnalysisResponse,
)
def get_inventory_analysis(
    restaurant_id: int,
    db: Annotated[Session, Depends(get_db)],
    horizon: Annotated[int, Query(ge=1, le=30)] = DEFAULT_INVENTORY_HORIZON,
    start_date: date | None = None,
) -> InventoryAnalysisResponse:
    restaurant = db.get(Restaurant, restaurant_id)

    if restaurant is None:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    try:
        analysis = analyze_inventory(
            session=db,
            restaurant_id=restaurant_id,
            horizon=horizon,
            start_date=start_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return InventoryAnalysisResponse.model_validate(analysis)
