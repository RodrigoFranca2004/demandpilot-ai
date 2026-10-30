from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import DailySale, Product
from app.schemas.products import DailySaleResponse, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductResponse])
def list_products(
    db: Annotated[Session, Depends(get_db)],
) -> list[ProductResponse]:
    products = db.scalars(select(Product).order_by(Product.id)).all()

    return [ProductResponse.model_validate(product) for product in products]


@router.get(
    "/{product_id}/sales",
    response_model=list[DailySaleResponse],
)
def list_product_sales(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[DailySaleResponse]:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be on or before end_date",
        )

    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    query = select(DailySale).where(DailySale.product_id == product_id)

    if start_date is not None:
        query = query.where(DailySale.sale_date >= start_date)

    if end_date is not None:
        query = query.where(DailySale.sale_date <= end_date)

    sales = db.scalars(query.order_by(DailySale.sale_date)).all()

    return [DailySaleResponse.model_validate(sale) for sale in sales]
