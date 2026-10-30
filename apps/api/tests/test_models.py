from datetime import date

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, DailySale, Product, Restaurant


def test_schema_creates_expected_tables() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    try:
        Base.metadata.create_all(engine)

        table_names = set(inspect(engine).get_table_names())

        assert table_names == {
            "restaurants",
            "products",
            "ingredients",
            "recipe_items",
            "daily_sales",
            "inventory",
        }
    finally:
        engine.dispose()


def test_daily_sales_reject_negative_quantity() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as session:
            restaurant = Restaurant(name="Demo Restaurant")
            session.add(restaurant)
            session.flush()

            product = Product(
                restaurant_id=restaurant.id,
                name="Burger",
            )
            session.add(product)
            session.flush()

            sale = DailySale(
                product_id=product.id,
                sale_date=date(2026, 1, 1),
                quantity=-1,
            )
            session.add(sale)

            with pytest.raises(IntegrityError):
                session.commit()
    finally:
        engine.dispose()
