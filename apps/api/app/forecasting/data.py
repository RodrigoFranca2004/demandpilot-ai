import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailySale


def load_sales_history(
    session: Session,
    product_id: int,
) -> pd.DataFrame:
    sales = session.scalars(
        select(DailySale)
        .where(DailySale.product_id == product_id)
        .order_by(DailySale.sale_date)
    ).all()

    return pd.DataFrame(
        [(sale.sale_date, sale.quantity) for sale in sales],
        columns=["sale_date", "quantity"],
    )
